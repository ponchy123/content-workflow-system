<template>
  <div class="product-list-container">
    <page-header title="产品管理" subtitle="管理所有产品信息和费率配置">
      <template #actions>
        <div class="upload-section">
          <el-button type="primary" @click="showUploadTips">
            <el-icon><Upload /></el-icon>上传产品Excel
          </el-button>
          <el-button type="success" @click="handleDownloadTemplate">
            <el-icon><Download /></el-icon>下载模板
          </el-button>
          <el-button type="info" plain @click="templatePreviewVisible = true">
            <el-icon><View /></el-icon>模板预览
          </el-button>
          <el-upload
            ref="uploadRef"
            class="excel-uploader"
            :action="'/api/v1/products/products/upload_product_excel/'"
            :headers="uploadHeaders"
            :before-upload="beforeUpload"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :show-file-list="true"
            :auto-upload="false"
            accept=".xlsx,.xls"
            style="display: none"
          >
            <template #tip>
              <div v-if="hasSelectedFile" style="margin-top: 10px;">
                <el-button type="success" @click="submitUpload">开始上传</el-button>
                <span style="margin-left: 10px;">已选择文件，点击"开始上传"按钮提交</span>
              </div>
            </template>
          </el-upload>
        </div>
        <el-button type="primary" @click="handleAdd" :icon="Plus">新增产品</el-button>
        <el-button @click="refreshList" :icon="Refresh">刷新</el-button>
      </template>
    </page-header>

    <!-- 筛选表单 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="产品名称">
          <el-input v-model="filterForm.name" placeholder="请输入产品名称" clearable />
        </el-form-item>
        <el-form-item label="服务商">
          <el-select v-model="filterForm.provider" placeholder="请选择服务商" clearable>
            <el-option v-for="item in providers" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="filterForm.showAll" label="显示所有产品" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 产品列表 -->
    <el-card class="product-card">
      <el-table 
        :data="productList" 
        style="width: 100%"
        v-loading="loading"
        border 
      >
        <!-- 产品名称列 -->
        <el-table-column prop="product_name" label="产品名称" min-width="180">
          <template #default="scope">
            <el-link type="primary" @click="viewDetail(scope.row.product_id)">
              {{ scope.row.product_name || scope.row.name }}
            </el-link>
          </template>
        </el-table-column>
        
        <!-- 服务商列 -->
        <el-table-column prop="provider_name" label="服务商" min-width="120" />
        
        <!-- 国家列 -->
        <el-table-column prop="country" label="国家" min-width="100" />
        
        <!-- 货币列 -->
        <el-table-column prop="currency" label="货币" min-width="80" />
        
        <!-- 状态列 -->
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === true ? 'success' : 'danger'">
              {{ scope.row.status === true ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <!-- 生效日期列 -->
        <el-table-column prop="effective_date" label="生效日期" min-width="120">
          <template #default="scope">
            {{ formatDate(scope.row.effective_date) }}
          </template>
        </el-table-column>
        
        <!-- 失效日期列 -->
        <el-table-column prop="expiration_date" label="失效日期" min-width="120">
          <template #default="scope">
            {{ formatDate(scope.row.expiration_date) }}
          </template>
        </el-table-column>
        
        <!-- 操作列 -->
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="viewDetail(scope.row.product_id)">详情</el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="handleDeleteProduct(scope.row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 模板预览对话框 -->
    <el-dialog
      v-model="templatePreviewVisible"
      title="产品Excel模板预览"
      width="1000px"
      class="template-preview-dialog"
      fullscreen
    >
      <div class="template-info">
        <p>产品Excel模板包含以下三个工作表，组成一个完整的产品报价单。<strong>标红</strong>的字段为必填项</p>
      </div>
      
      <!-- 字段说明表格 -->
      <el-tabs v-model="activeTabName" class="demo-tabs">
        <!-- 基本信息表 -->
        <el-tab-pane label="1. 基本信息表" name="basic">
          <div class="field-table-container">
            <table class="field-table">
              <thead>
                <tr>
                  <th>产品名称</th>
                  <th>服务商</th>
                  <th>体积重系数</th>
                  <th>体积重系数单位</th>
                  <th>生效日期</th>
                  <th>失效日期</th>
                  <th>国家</th>
                  <th>币种</th>
                  <th>描述</th>
                  <th>状态</th>
                  <th>启用开始日期</th>
                  <th>启用结束日期</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>FEDEX JCF</td>
                  <td>FEDEX</td>
                  <td>200</td>
                  <td>lb/in³</td>
                  <td>2023/1/1</td>
                  <td>2023/12/31</td>
                  <td>美国</td>
                  <td>USD</td>
                  <td>1. 计费重量：体积重量与实际重量相比，取大值。2. 体积重(磅)=长×宽×高(英寸)/250。3. 燃油附加费(Fuel Surcharge)=(基础派送运费 + 其他附加费)*燃油附加费率。按FedEx官网Ground燃油费率计算，燃油费率查询网址：https://www.fedex.com/en-us/shipping/fuel-surcharge.html。4. 附加费/增值服务标准根据东 运营商调整，有产生的除以下列出的项目外的其他服务，费用实报实销。5.本报价生效时间：2024/01/01至另行通知。5.同一包裹符合不可发包裹附加费中的任一条件，此类包裹不可发；若向Fedex交付符合不可发条件的包裹，附加费为每件收费，且可能被拒收</td>
                  <td>启用</td>
                  <td>2023/1/6</td>
                  <td>2023/12/20</td>
                </tr>
              </tbody>
            </table>
            <div class="table-description">
              <h4>字段说明：</h4>
              <ul>
                <li><span class="required">产品名称</span>：产品的完整名称</li>
                <li><span class="required">服务商</span>：物流服务提供商，必须是系统支持的服务商名称之一</li>
                <li><span class="required">体积重系数</span>：计算体积重的系数，正数，最多2位小数</li>
                <li><span class="required">体积重系数单位</span>：体积重计算使用的单位，如lb/in³</li>
                <li><span class="required">生效日期</span>：产品费率生效日期，格式：YYYY/M/D</li>
                <li>失效日期：产品费率失效日期，格式：YYYY/M/D</li>
                <li>国家：服务适用的国家</li>
                <li>币种：费率使用的币种，三字符币种代码(ISO 4217标准)</li>
                <li>描述：产品的详细说明，可包含计费规则等信息</li>
                <li>状态：产品是否启用，"启用"或"禁用"</li>
                <li>启用开始日期：产品启用的开始日期，格式：YYYY/M/D</li>
                <li>启用结束日期：产品启用的结束日期，格式：YYYY/M/D</li>
              </ul>
            </div>
          </div>
        </el-tab-pane>
        
        <!-- 基础费用表 -->
        <el-tab-pane label="2. 基础费用表" name="baserate">
          <div class="field-table-container">
            <table class="field-table">
                  <thead>
                    <tr>
                      <th>重量</th>
                      <th>单位</th>
                      <th>计价类型</th>
                      <th>Zone1基础价格</th>
                      <th>Zone2基础价格</th>
                      <th>Zone3基础价格</th>
                      <th>Zone4基础价格</th>
                      <th>Zone5基础价格</th>
                      <th>Zone6基础价格</th>
                      <th>Zone7基础价格</th>
                      <th>Zone8基础价格</th>
                      <th>Zone17基础价格</th>
                      <th>Zone1单位重量价格</th>
                      <th>Zone2单位重量价格</th>
                      <th>Zone3单位重量价格</th>
                      <th>Zone4单位重量价格</th>
                      <th>Zone5单位重量价格</th>
                      <th>Zone6单位重量价格</th>
                      <th>Zone7单位重量价格</th>
                      <th>Zone8单位重量价格</th>
                      <th>Zone17单位重量价格</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>2</td>
                      <td>oz</td>
                      <td>STEP</td>
                      <td>1.25</td>
                      <td>1.25</td>
                      <td>7.5</td>
                      <td>7.95</td>
                      <td>8.25</td>
                      <td>8.6</td>
                      <td>8.85</td>
                      <td>9.2</td>
                      <td>9.5</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                    </tr>
                    <tr>
                      <td>4</td>
                      <td>oz</td>
                      <td>STEP</td>
                      <td>2.4</td>
                      <td>2.4</td>
                      <td>7.65</td>
                      <td>8.1</td>
                      <td>8.4</td>
                      <td>8.75</td>
                      <td>9.05</td>
                      <td>9.45</td>
                      <td>9.8</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                    </tr>
                    <tr>
                      <td>6</td>
                      <td>oz</td>
                      <td>STEP</td>
                      <td>3.55</td>
                      <td>3.55</td>
                      <td>7.8</td>
                      <td>8.25</td>
                      <td>8.55</td>
                      <td>8.9</td>
                      <td>9.25</td>
                      <td>9.7</td>
                      <td>10.7</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                    </tr>
                    <tr>
                      <td>15.99</td>
                      <td>oz</td>
                      <td>STEP</td>
                      <td>7.7</td>
                      <td>7.7</td>
                      <td>7.95</td>
                      <td>8.4</td>
                      <td>8.7</td>
                      <td>9.05</td>
                      <td>9.45</td>
                      <td>9.95</td>
                      <td>10.95</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                    </tr>
                    <tr>
                      <td>1</td>
                      <td>lb</td>
                      <td>STEP</td>
                      <td>8.68</td>
                      <td>8.68</td>
                      <td>8.68</td>
                      <td>8.68</td>
                      <td>8.68</td>
                      <td>8.68</td>
                      <td>9.1</td>
                      <td>10.25</td>
                      <td>11.25</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                      <td>0</td>
                    </tr>
                    <tr>
                      <td>2</td>
                      <td>lb</td>
                      <td>LINEAR</td>
                      <td>9.35</td>
                      <td>9.35</td>
                      <td>9.45</td>
                      <td>9.65</td>
                      <td>10.2</td>
                      <td>11.35</td>
                      <td>12.8</td>
                      <td>14.5</td>
                      <td>15.5</td>
                      <td>2.5</td>
                      <td>2.5</td>
                      <td>2.55</td>
                      <td>2.75</td>
                      <td>2.85</td>
                      <td>2.95</td>
                      <td>2.75</td>
                      <td>2.55</td>
                      <td>2.98</td>
                    </tr>
                  </tbody>
                </table>
            <div class="table-description">
              <h4>字段说明：</h4>
              <ul>
                <li><span class="required">重量</span>：运输包裹的重量值</li>
                <li><span class="required">单位</span>：重量单位，如oz(盎司)、lb(磅)</li>
                <li><span class="required">计价类型</span>：STEP(阶梯式)或LINEAR(线性)</li>
                <li><span class="required">Zone1-Zone17基础价格</span>：不同区域的基础运费，单位为所选币种</li>
                <li><span class="required">Zone1-Zone17单位重量价格</span>：各区域每单位重量的增量费用，仅在LINEAR计价类型下使用</li>
              </ul>
              <p>注：</p>
              <p>基础费用表按照重量和区域定义基本运费，每个Zone代表不同的配送区域</p>
              <p>重量：运输包裹的实际重量值</p>
              <p>单位：重量单位，Kilos(公斤)、lb(磅)</p>
              <p>Zone1-Zone17：不同区域的基础运费，单位为所选币种</p>
            </div>
          </div>
        </el-tab-pane>

        <!-- 附加费表 -->
        <el-tab-pane label="3. 附加费表" name="surcharge">
          <div class="field-table-container">
            <table class="field-table">
                <thead>
                  <tr>
                    <th>附加费类型</th>
                    <th>子类型</th>
                    <th>条件描述</th>
                  <th>Zone1</th>
                    <th>Zone2</th>
                    <th>Zone3</th>
                    <th>Zone4</th>
                    <th>Zone5</th>
                    <th>Zone6</th>
                    <th>Zone7</th>
                    <th>Zone8</th>
                  <th>Zone17</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                  <td>额外处理费(Additional Handling Surcharge)</td>
                  <td>a)额外处理费A-weight</td>
                  <td>55磅 < 实际重量 < 155磅</td>
                  <td>-</td>
                  <td>5</td>
                  <td>5</td>
                    <td>8.49</td>
                    <td>8.49</td>
                    <td>8.96</td>
                    <td>8.96</td>
                    <td>9.66</td>
                  <td>10.66</td>
                  </tr>
                  <tr>
                  <td>额外处理费(Additional Handling Surcharge)</td>
                  <td>b)额外处理费B-length</td>
                    <td>48英寸 < 最长边 ≤ 96英寸</td>
                  <td>5.42</td>
                    <td>5.42</td>
                    <td>5.88</td>
                    <td>5.88</td>
                    <td>6.35</td>
                    <td>6.35</td>
                    <td>6.99</td>
                    <td>6.99</td>
                  <td>7.99</td>
                  </tr>
                  <tr>
                  <td>额外处理费(Additional Handling Surcharge)</td>
                  <td>c)额外处理费C-length+girth</td>
                    <td>105英寸 < 长+周长[2*(宽+高)] ≤ 130英寸</td>
                  <td>5.42</td>
                    <td>5.42</td>
                    <td>5.88</td>
                    <td>5.88</td>
                    <td>6.35</td>
                    <td>6.35</td>
                    <td>6.99</td>
                    <td>6.99</td>
                  <td>8.99</td>
                  </tr>
                  <tr>
                  <td>额外处理费(Additional Handling Surcharge)</td>
                  <td>d)额外处理费D-width</td>
                    <td>第二长边 > 30英寸</td>
                  <td>5.42</td>
                    <td>5.42</td>
                    <td>5.88</td>
                    <td>5.88</td>
                    <td>6.35</td>
                    <td>6.35</td>
                    <td>6.99</td>
                    <td>6.99</td>
                  <td>7.99</td>
                  </tr>
                  <tr>
                  <td>额外处理费(Additional Handling Surcharge)</td>
                  <td>e)其它额外处理费-packaging</td>
                  <td>包装未采行任何包装或包材质为泡沫、金属、木材、布料、皮革、隔气或易损易碎的包装，如果架、隔柱体、圆柱体(桶装、罐装、管状)、外包装形状被像信任何包装的包装，因任何原因和UPS在送达过程中重新包装。</td>
                    <td>4.94</td>
                  <td>4.99</td>
                  <td>5.88</td>
                  <td>5.99</td>
                  <td>6.35</td>
                  <td>6.44</td>
                  <td>6.99</td>
                  <td>7.11</td>
                  <td>8.11</td>
                  </tr>
                  <tr>
                  <td>超大超尺寸费(Oversize-商业地址)</td>
                  <td>a)超大超尺寸费A</td>
                  <td>实际重量 ≥ 150磅，且96英寸 < 最长边 ≤ 108英寸</td>
                  <td>42.88</td>
                  <td>43.32</td>
                  <td>44.99</td>
                  <td>48.86</td>
                  <td>48.89</td>
                  <td>49.66</td>
                  <td>51.22</td>
                  <td>52.88</td>
                  <td>52.88</td>
                  </tr>
                  <tr>
                  <td>超大超尺寸费(Oversize-商业地址)</td>
                  <td>b)超大超尺寸费B</td>
                    <td>实际重量 < 150磅，且96英寸 < 最长边 ≤ 108英寸</td>
                  <td>42.88</td>
                  <td>43.32</td>
                  <td>44.99</td>
                  <td>48.86</td>
                  <td>48.89</td>
                  <td>49.66</td>
                  <td>51.22</td>
                  <td>52.88</td>
                  <td>52.88</td>
                  </tr>
                  <tr>
                  <td>超大超尺寸费(Oversize-商业地址)</td>
                  <td>c)超大超尺寸费C</td>
                  <td>尺寸符合Oversize条款的计费重量时，不足90磅按90磅计，实际重量 ≥ 150磅，且130英寸 < 长+周长[2*(宽+高)] ≤ 165英寸</td>
                  <td>42.88</td>
                  <td>43.32</td>
                  <td>44.99</td>
                  <td>48.86</td>
                  <td>48.89</td>
                  <td>49.66</td>
                  <td>51.22</td>
                  <td>52.88</td>
                  <td>52.88</td>
                  </tr>
                  <tr>
                  <td>超大超尺寸费(Oversize-住宅地址)</td>
                  <td>a)超大超尺寸费A</td>
                  <td>实际重量 ≥ 150磅，且96英寸 < 最长边 ≤ 108英寸</td>
                  <td>47.88</td>
                  <td>48.32</td>
                  <td>49.99</td>
                  <td>53.86</td>
                  <td>54.89</td>
                  <td>55.66</td>
                  <td>56.22</td>
                  <td>57.88</td>
                  <td>57.88</td>
                  </tr>
                  <tr>
                  <td>超大超尺寸费(Oversize-住宅地址)</td>
                  <td>b)超大超尺寸费B</td>
                    <td>实际重量 < 150磅，且96英寸 < 最长边 ≤ 108英寸</td>
                  <td>47.88</td>
                  <td>48.32</td>
                  <td>49.99</td>
                  <td>53.86</td>
                  <td>54.89</td>
                  <td>55.66</td>
                  <td>56.22</td>
                  <td>57.88</td>
                  <td>57.88</td>
                  </tr>
                  <tr>
                  <td>超大超尺寸费(Oversize-住宅地址)</td>
                  <td>c)超大超尺寸费C</td>
                  <td>尺寸符合Oversize条款的计费重量时，不足90磅按90磅计，实际重量 ≥ 150磅，且130英寸 < 长+周长[2*(宽+高)] ≤ 165英寸</td>
                  <td>47.88</td>
                  <td>48.32</td>
                  <td>49.99</td>
                  <td>53.86</td>
                  <td>54.89</td>
                  <td>55.66</td>
                  <td>56.22</td>
                  <td>57.88</td>
                  <td>57.88</td>
                  </tr>
                  <tr>
                  <td>住宅地址附加费(Residential Surcharge)</td>
                    <td>FedEx Home Delivery</td>
                  <td>FedEx Home Delivery</td>
                  <td>2.87</td>
                  <td>2.87</td>
                    <td>2.87</td>
                    <td>2.87</td>
                    <td>2.87</td>
                    <td>2.87</td>
                    <td>2.87</td>
                    <td>2.87</td>
                    <td>2.87</td>
                  </tr>
                  <tr>
                  <td>住宅地址附加费(Residential Surcharge)</td>
                    <td>FedEx Commercial Ground</td>
                    <td>如果产品超过70磅，将由Ground服务派送至住宅地址，而非Home服务</td>
                    <td>6.45</td>
                    <td>6.45</td>
                    <td>6.45</td>
                    <td>6.45</td>
                    <td>6.45</td>
                    <td>6.45</td>
                    <td>6.45</td>
                    <td>6.45</td>
                    <td>6.45</td>
                  </tr>
                  <tr>
                  <td>偏远地区附加费(Delivery Area Surcharge)</td>
                  <td>Commercial (FedEx Ground)</td>
                  <td>Commercial (FedEx Ground)</td>
                  <td>2.12</td>
                  <td>2.12</td>
                    <td>2.12</td>
                    <td>2.12</td>
                    <td>2.12</td>
                    <td>2.12</td>
                    <td>2.12</td>
                    <td>2.12</td>
                    <td>2.12</td>
                  </tr>
                  <tr>
                  <td>偏远地区附加费(Delivery Area Surcharge)</td>
                  <td>Extended Commercial (FedEx Ground)</td>
                  <td>Extended Commercial (FedEx Ground)</td>
                  <td>2.52</td>
                  <td>2.52</td>
                    <td>2.52</td>
                    <td>2.52</td>
                    <td>2.52</td>
                    <td>2.52</td>
                    <td>2.52</td>
                    <td>2.52</td>
                    <td>2.52</td>
                  </tr>
                  <tr>
                  <td>偏远地区附加费(Delivery Area Surcharge)</td>
                  <td>Residential (FedEx Ground)</td>
                  <td>Residential (FedEx Ground)</td>
                  <td>6.7</td>
                  <td>6.7</td>
                  <td>6.7</td>
                  <td>6.7</td>
                  <td>6.7</td>
                  <td>6.7</td>
                  <td>6.7</td>
                  <td>6.7</td>
                  <td>6.7</td>
                  </tr>
                  <tr>
                  <td>偏远地区附加费(Delivery Area Surcharge)</td>
                  <td>Extended Residential (FedEx Ground)</td>
                  <td>Extended Residential (FedEx Ground)</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                </tr>
                <tr>
                  <td>偏远地区附加费(Delivery Area Surcharge)</td>
                    <td>Residential (FedEx Home Delivery)</td>
                  <td>Residential (FedEx Home Delivery)</td>
                  <td>2.88</td>
                  <td>2.88</td>
                    <td>2.88</td>
                    <td>2.88</td>
                    <td>2.88</td>
                    <td>2.88</td>
                    <td>2.88</td>
                    <td>2.88</td>
                    <td>2.88</td>
                  </tr>
                  <tr>
                  <td>偏远地区附加费(Delivery Area Surcharge)</td>
                    <td>Extended Residential (FedEx Home Delivery)</td>
                  <td>Extended Residential (FedEx Home Delivery)</td>
                  <td>3.7</td>
                  <td>3.7</td>
                  <td>3.7</td>
                  <td>3.7</td>
                  <td>3.7</td>
                  <td>3.7</td>
                  <td>3.7</td>
                  <td>3.7</td>
                  <td>3.7</td>
                  </tr>
                  <tr>
                  <td>偏远地区附加费(Delivery Area Surcharge)</td>
                  <td>极偏远费 -DAS Remote Comm(FedEx Ground)</td>
                  <td>极偏远费 -DAS Remote Comm(FedEx Ground)</td>
                  <td>6.47</td>
                  <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                  </tr>
                  <tr>
                  <td>偏远地区附加费(Delivery Area Surcharge)</td>
                  <td>极偏远费 -DAS Remote Resi (FedEx Ground)</td>
                  <td>极偏远费 -DAS Remote Resi (FedEx Ground)</td>
                  <td>16</td>
                  <td>16</td>
                  <td>16</td>
                  <td>16</td>
                  <td>16</td>
                  <td>16</td>
                  <td>16</td>
                  <td>16</td>
                  <td>16</td>
                  </tr>
                  <tr>
                  <td>偏远地区附加费(Delivery Area Surcharge)</td>
                  <td>极偏远费 -DAS Remote Resi (FedEx Home Delivery)</td>
                  <td>极偏远费 -DAS Remote Resi (FedEx Home Delivery)</td>
                  <td>6.47</td>
                  <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                    <td>6.47</td>
                  </tr>
                  <tr>
                  <td>地址校验更改</td>
                  <td>a)FedEx主动修改地址(Address Correction)</td>
                  <td>地址填写错误，FedEx修改地址，以账单为准</td>
                  <td>27</td>
                  <td>27</td>
                  <td>27</td>
                  <td>27</td>
                  <td>27</td>
                  <td>27</td>
                  <td>27</td>
                  <td>27</td>
                  <td>27</td>
                  </tr>
                  <tr>
                  <td>地址校验更改</td>
                  <td>b)收件人/发件人主动修改(Delivery intercept)</td>
                  <td>收件人/发件人修改，包含修改地址、派送时间等</td>
                  <td>29.9</td>
                  <td>29.9</td>
                  <td>29.9</td>
                  <td>29.9</td>
                  <td>29.9</td>
                  <td>29.9</td>
                  <td>29.9</td>
                  <td>29.9</td>
                  <td>29.9</td>
                  </tr>
                  <tr>
                  <td>签名签收</td>
                  <td>Indirect Signature Required</td>
                  <td>Indirect Signature Required</td>
                  <td>0</td>
                  <td>0</td>
                  <td>0</td>
                  <td>0</td>
                  <td>0</td>
                  <td>0</td>
                  <td>0</td>
                  <td>0</td>
                  <td>0</td>
                  </tr>
                  <tr>
                  <td>签名签收</td>
                  <td>Direct Signature Required</td>
                  <td>Direct Signature Required</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  <td>8.8</td>
                  </tr>
                  <tr>
                  <td>签名签收</td>
                  <td>Adult Signature Required</td>
                  <td>Adult Signature Required</td>
                  <td>9.9</td>
                  <td>9.9</td>
                  <td>9.9</td>
                  <td>9.9</td>
                  <td>9.9</td>
                  <td>9.9</td>
                  <td>9.9</td>
                  <td>9.9</td>
                  <td>9.9</td>
                  </tr>
                  <tr>
                  <td>运费复合费(Shipping Charge Correction)</td>
                  <td>运费复合费(Shipping Charge Correction)</td>
                  <td>运费复合费(Shipping Charge Correction)</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  </tr>
                  <tr>
                  <td>原件退回</td>
                  <td>原件退回</td>
                  <td>预报重量与尺寸与实际不符时，按USD 1.00每件或实件运费的6%, 两者的最大值收取</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  <td>1</td>
                  </tr>
                  <tr>
                  <td>不可发包裹(Unauthorized)</td>
                  <td>a)不可发包裹A-weight</td>
                  <td>a)实重 > 150磅</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  </tr>
                  <tr>
                  <td>不可发包裹(Unauthorized)</td>
                  <td>b)不可发包裹B-length</td>
                  <td>b)最长边 > 108英寸</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  </tr>
                  <tr>
                  <td>不可发包裹(Unauthorized)</td>
                  <td>c)不可发包裹C-length+girth</td>
                  <td>c)长+周长 > 165英寸</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  <td>1325</td>
                  </tr>
                </tbody>
              </table>
            <div class="table-description">
              <h4>字段说明：</h4>
              <ul>
                <li><span class="required">附加费类型</span>：附加费的主分类名称</li>
                <li><span class="required">子类型</span>：附加费的细分类型</li>
                <li><span class="required">条件描述</span>：触发该附加费的条件说明</li>
                <li><span class="required">Zone1-Zone17</span>：各区域的附加费金额</li>
              </ul>
              <p>注：附加费按照不同条件和分区收取，可能依据重量、尺寸、特殊处理需求等因素收费</p>
            </div>
          </div>
        </el-tab-pane>
        
        <!-- 旺季附加费表 -->
        <el-tab-pane label="4. 旺季附加费表" name="peakseason">
          <div class="field-table-container">
            <table class="field-table">
                <thead>
                  <tr>
                    <th>附加费类型</th>
                    <th>开始日期</th>
                    <th>结束日期</th>
                    <th>费用金额</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                  <td>额外处理费(Additional Handling Surcharge)</td>
                  <td>2023/10/2</td>
                  <td>2023/11/24</td>
                  <td>3.68</td>
                  </tr>
                  <tr>
                  <td>额外处理费(Additional Handling Surcharge)</td>
                  <td>2023/11/25</td>
                  <td>2023/12/31</td>
                    <td>5.85</td>
                  </tr>
                <tr>
                  <td>超大超尺寸费(Oversize-商业地址)</td>
                  <td>2023/10/2</td>
                  <td>2023/11/24</td>
                  <td>43.68</td>
                </tr>
                <tr>
                  <td>超大超尺寸费(Oversize-商业地址)</td>
                  <td>2023/11/25</td>
                  <td>2023/12/31</td>
                  <td>45.85</td>
                </tr>
                <tr>
                  <td>超大超尺寸费(Oversize-住宅地址)</td>
                  <td>2023/10/2</td>
                  <td>2023/11/24</td>
                  <td>43.68</td>
                </tr>
                <tr>
                  <td>超大超尺寸费(Oversize-住宅地址)</td>
                  <td>2023/11/25</td>
                  <td>2023/12/31</td>
                  <td>45.85</td>
                </tr>
                <tr>
                  <td>住宅地址附加费(Residential Surcharge)</td>
                  <td>2023/10/2</td>
                  <td>2023/11/24</td>
                  <td>1.68</td>
                </tr>
                <tr>
                  <td>住宅地址附加费(Residential Surcharge)</td>
                  <td>2023/11/25</td>
                  <td>2023/12/31</td>
                  <td>1.85</td>
                </tr>
                <tr>
                  <td>不可发包裹(Unauthorized)</td>
                  <td>2023/10/2</td>
                  <td>2023/11/24</td>
                  <td>575</td>
                </tr>
                <tr>
                  <td>不可发包裹(Unauthorized)</td>
                  <td>2023/11/25</td>
                  <td>2023/12/31</td>
                  <td>475</td>
                </tr>
              </tbody>
            </table>
            <div class="table-description">
              <h4>字段说明：</h4>
              <ul>
                <li><span class="required">附加费类型</span>：与标准附加费对应的旺季附加费类型</li>
                <li><span class="required">开始日期</span>：旺季附加费开始适用的日期</li>
                <li><span class="required">结束日期</span>：旺季附加费结束的日期</li>
                <li><span class="required">费用金额</span>：旺季期间适用的附加费金额</li>
              </ul>
              <p>注：旺季附加费通常在节日或特殊时段收取，费率高于常规附加费</p>
          </div>
          </div>
        </el-tab-pane>

        <!-- 重量段表 - 已被删除，融合到基础费用表 -->
        
      </el-tabs>
      
      <div class="dialog-footer">
        <el-button @click="templatePreviewVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleDownloadTemplate">
          <el-icon><Download /></el-icon>下载完整模板
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, reactive, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus';
import PageHeader from '@/components/PageHeader.vue';
import { Plus, Refresh, Upload, Download, View } from '@element-plus/icons-vue';
import { getProducts, getProductsList, deleteProduct } from '@/api/products';
import axios from 'axios';
import { axiosInstance } from '@/api/core/request';
import type { UploadProps } from 'element-plus';
import type { Product, ExtendedProduct } from '@/types/product';

// 从本地存储获取JWT token
const getToken = () => {
  return localStorage.getItem('access_token');
};

// 定义响应式状态
const router = useRouter();
const loading = ref(false);
const productList = ref<ExtendedProduct[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);
const uploadRef = ref();
const templatePreviewVisible = ref(false);
const activeTabName = ref('basic');
const hasSelectedFile = ref(false); // 是否已选择文件

// 服务商列表
const providers = ref<string[]>([
  'UPS', 'FedEx', 'DHL', 'TNT', 'EMS', '顺丰', '中通', '圆通', '申通', '韵达'
]);

// 上传headers
const uploadHeaders = {
  Authorization: `Bearer ${getToken()}`
};

// 筛选表单
const filterForm = reactive({
  name: '',
  provider: '',
  showAll: true,  // 默认显示所有产品
});

// 格式化日期
const formatDate = (date: string | null) => {
  if (!date) return '-';
  return new Date(date).toLocaleDateString();
};

// 获取产品列表数据
const fetchProducts = async () => {
  try {
    loading.value = true;
    console.log('开始请求产品列表，参数:', {
      page: currentPage.value,
      pageSize: pageSize.value,
      search: filterForm.name,
      provider: filterForm.provider,
      show_all: filterForm.showAll
    });

    // 尝试使用新的专用API方法
    const response = await getProductsList({
      page: currentPage.value,
      pageSize: pageSize.value,
      search: filterForm.name,
      provider: filterForm.provider,
      show_all: filterForm.showAll
    });

    console.log('获取产品列表响应完整数据:', response);

    // 根据返回的数据结构判断如何处理
    if (response && 'results' in response && Array.isArray(response.results)) {
      // 直接返回了标准分页格式的数据
      console.log('直接获取到分页数据，results字段在response根级别');
      productList.value = response.results as ExtendedProduct[];
      total.value = ('count' in response ? response.count as number : response.results.length);
    } else if (response && response.data && 'results' in response.data && Array.isArray(response.data.results)) {
      // 数据在response.data中（标准axios返回）
      console.log('检测到响应data中包含results字段');
      productList.value = response.data.results as ExtendedProduct[];
      total.value = response.data.count || response.data.results.length;
    } else if (response && Array.isArray(response)) {
      // 直接返回了数组
      console.log('检测到响应直接是数组');
      productList.value = response as ExtendedProduct[];
      total.value = response.length;
    } else if (response && response.data && Array.isArray(response.data)) {
      // 返回的是数组，在data中
      console.log('检测到响应data是数组');
      productList.value = response.data as ExtendedProduct[];
      total.value = response.data.length;
    } else if (response && response.data && response.data.products) {
      // 包含在products字段中
      console.log('检测到响应包含products字段');
      productList.value = response.data.products as ExtendedProduct[];
      total.value = response.data.count || response.data.products.length;
    } else {
      // 尝试将对象值转为数组
      console.log('尝试从其他格式提取数据');
      const dataSource = response.data || response;
      const productsArray = Object.values(dataSource).filter(item => 
        typeof item === 'object' && item !== null && !Array.isArray(item)
      ) as ExtendedProduct[];
      
      if (productsArray.length > 0) {
        productList.value = productsArray;
        total.value = productsArray.length;
      } else {
        console.warn('未能识别API响应格式:', response);
        productList.value = [];
        total.value = 0;
      }
    }
    
    console.log('处理后的产品列表:', productList.value);
    console.log('产品列表数量:', productList.value.length);
    
    // 更新服务商列表
    const uniqueProviders = new Set<string>();
    productList.value.forEach(product => {
      if (product.provider_name) {
        uniqueProviders.add(product.provider_name);
      }
    });
    providers.value = Array.from(uniqueProviders);
  } catch (error) {
    console.error('获取产品列表失败:', error);
    ElMessage.error('获取产品列表失败，请稍后重试');
    productList.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

// 显示上传提示
const showUploadTips = () => {
  // 显示上传对话框
  ElMessageBox.alert(
    `<div class="upload-tips">
      <h4>Excel上传说明：</h4>
      <ol>
        <li>Excel文件必须按照模板格式填写。</li>
        <li>请确保基本信息表、基础费用表、附加费表和旺季附加费表的数据完整。</li>
        <li>上传前请核对所有数据的准确性，尤其是价格和日期信息。</li>
        <li>文件大小不能超过10MB。</li>
      </ol>
    </div>`,
    '上传产品Excel',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '选择文件',
      callback: (action: string) => {
        if (action === 'confirm') {
          // 点击确认后，触发文件选择
          chooseUploadFile();
        }
      }
    }
  );
};

// 选择上传文件
const chooseUploadFile = () => {
  // 找到上传组件内部的文件选择input并触发点击
  if (uploadRef.value) {
    const fileInput = uploadRef.value.$el.querySelector('input[type="file"]');
    if (fileInput) {
      fileInput.click();
      // 监听文件选择变化
      fileInput.onchange = () => {
        hasSelectedFile.value = fileInput.files && fileInput.files.length > 0;
        if (hasSelectedFile.value) {
          // 显示确认上传对话框
          showUploadConfirmDialog(fileInput.files[0].name);
        }
      };
    }
  }
};

// 显示确认上传对话框
const showUploadConfirmDialog = (fileName: string) => {
  ElMessageBox.confirm(
    `<div>
      <p>已选择文件: <strong>${fileName}</strong></p>
      <p>确认上传此文件吗？上传后系统将自动处理数据。</p>
    </div>`,
    '确认上传',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '确认上传',
      cancelButtonText: '取消',
      type: 'info',
      callback: (action: string) => {
        if (action === 'confirm') {
          submitUpload();
        } else {
          // 取消上传，清空选择
          hasSelectedFile.value = false;
          if (uploadRef.value) {
            uploadRef.value.clearFiles();
          }
        }
      }
    }
  );
};

// 上传前验证
const beforeUpload = (file: File) => {
  // 文件类型检查
  const isExcel = file.type === 'application/vnd.ms-excel' || 
                 file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                 file.name.endsWith('.xlsx') ||
                 file.name.endsWith('.xls');
  
  if (!isExcel) {
    ElMessage.error('只能上传Excel文件!');
    return false;
  }
  
  // 文件大小检查
  const isLt10M = file.size / 1024 / 1024 < 10;
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过10MB!');
    return false;
  }
  
  // 设置已选择文件标志
  hasSelectedFile.value = true;
  console.log('文件已选择:', file.name);
  return true;
};

// 手动提交上传
const submitUpload = () => {
  if (!hasSelectedFile.value) {
    ElMessage.warning('请先选择Excel文件');
    return;
  }
  
  if (uploadRef.value) {
    uploadRef.value.submit();
    console.log('手动触发文件上传');
  }
};

// 上传成功处理
const handleUploadSuccess = (response: any) => {
  console.log('上传响应:', response);
  
  // 检查响应类型，处理不同格式的响应
  let actualResponse = response;
  if (response.data && (response.status === 200 || response.status === 'success')) {
    actualResponse = response.data;
  }
  
  console.log('处理后的响应:', actualResponse);
  
  // 无论结果如何，确保总是刷新产品列表
  // 使用setTimeout给后端一些时间处理数据
  setTimeout(() => {
    fetchProducts();
    console.log('产品列表已刷新');
  }, 500);
  
  // 显示上传结果消息
  if (actualResponse.message === 'Excel导入成功' || actualResponse.status === 'success') {
    // 处理统一格式的响应
    let resultsDetails = '';
    if (actualResponse.results) {
      // 处理新格式的响应
      const results = actualResponse.results;
      
      resultsDetails = Object.entries(results)
        .map(([key, value]: [string, any]) => {
          if (typeof value === 'object' && value !== null) {
            const successCount = value.success || 0;
            const errorCount = value.errors || 0;
            const totalCount = value.total || 0;
            return `${key}: 成功${successCount}/${totalCount}条`;
          }
          return `${key}: ${value}`;
        })
        .join('<br>');
    }
    
    // 显示成功消息
    ElMessageBox.alert(
      `<div>
        <p>Excel导入成功</p>
        ${resultsDetails ? `<p>详细信息:</p><div>${resultsDetails}</div>` : ''}
      </div>`,
      '导入结果',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '确定',
        type: 'success'
      }
    );
  } else {
    // 导入失败或错误
    let errorMessage = '导入失败';
    
    if (actualResponse.error) {
      errorMessage = actualResponse.error;
    } else if (actualResponse.message) {
      errorMessage = actualResponse.message;
    }
    
    ElMessageBox.alert(
      `<div>
        <p>${errorMessage}</p>
      </div>`,
      '导入结果',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '确定',
        type: 'error'
      }
    );
  }
  
  // 重置文件选择状态
  hasSelectedFile.value = false;
  if (uploadRef.value) {
    uploadRef.value.clearFiles();
  }
};

// 上传错误处理
const handleUploadError = (error: any) => {
  console.error('上传失败:', error);
  
  let errorMessage = '文件上传失败';
  
  // 尝试提取详细错误信息
  if (error.response && error.response.data) {
    // 后端返回的错误数据
    const responseData = error.response.data;
    
    if (typeof responseData === 'string') {
      errorMessage = responseData;
    } else if (responseData.message) {
      errorMessage = responseData.message;
    } else if (responseData.error) {
      errorMessage = responseData.error;
    } else if (responseData.detail) {
      errorMessage = responseData.detail;
    }
  } else if (error.message) {
    errorMessage = error.message;
  }
  
  ElMessage({
    message: `导入失败: ${errorMessage}`,
    type: 'error',
    duration: 5000,
    showClose: true
  });
  
  // 重置文件选择状态
  hasSelectedFile.value = false;
};

// 下载模板
const handleDownloadTemplate = () => {
  try {
    // 在下载前显示填表说明提示
    ElMessageBox.alert(
      `<div class="download-tips">
        <h4>填表说明：</h4>
        <ol>
          <li>基本信息表代表产品基本信息，所有字段都是填写。</li>
          <li>每个产品唯一标识是【产品名称】和【服务商】的组合，请确保在同一服务商下产品名称唯一。</li>
          <li>基础费用表中填写各区域的基础价格和单位重量价格。</li>
          <li>附加费表中填写各种附加费项目。</li>
          <li>旺季附加费表中填写临时性的旺季附加费。</li>
          <li>所有日期格式为YYYY/MM/DD。</li>
          <li>上传时系统会自动生成其他必要信息，无需手填。</li>
        </ol>
      </div>`,
      '下载前请注意',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '继续下载',
        callback: (action: string) => {
          if (action === 'confirm') {
            downloadTemplateFile();
          }
        }
      }
    );
  } catch (error) {
    console.error('下载模板失败:', error);
    ElMessage.error('下载模板失败，请稍后重试');
  }
};

// 实际下载模板文件
const downloadTemplateFile = () => {
  const token = getToken();
  // 使用原生fetch API下载模板
  fetch('/api/v1/products/products/download_product_template/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`下载失败: ${response.status} ${response.statusText}`);
    }
    return response.blob();
  })
  .then(blob => {
    // 创建一个blob链接
    const url = window.URL.createObjectURL(blob);
    
    // 创建一个隐藏的a标签用于下载
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', '产品导入模板.xlsx');
    document.body.appendChild(link);
    link.click();
    
    // 清理
    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);
    
    ElMessage.success('模板下载成功');
  })
  .catch(error => {
    console.error('下载模板失败:', error);
    ElMessage.error(`下载模板失败: ${error.message}`);
  });
};

// 刷新列表
const refreshList = () => {
  fetchProducts();
};

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1;
  fetchProducts();
};

// 重置筛选
const handleReset = () => {
  filterForm.name = '';
  filterForm.provider = '';
  filterForm.showAll = true;
  currentPage.value = 1;
  fetchProducts();
};

// 分页大小变化
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  fetchProducts();
};

// 当前页变化
const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  fetchProducts();
};

// 查看产品详情
const viewDetail = (id: string | number) => {
  console.log('查看产品详情，ID:', id);
  router.push(`/product/detail/${id}`);
};

// 添加产品
const handleAdd = () => {
  router.push('/product/create');
};

// 删除产品
const handleDeleteProduct = (row: any) => {
  ElMessageBox.confirm(
    `确定要删除产品 "${row.name || row.product_name}" 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
  .then(async () => {
    try {
      console.log('开始删除产品:', row);
      const productId = row.product_id;
      if (!productId) {
        ElMessage.error('无法获取产品ID');
        return;
      }
      
      await deleteProduct(productId);
      
      ElMessage({
        type: 'success',
        message: '删除成功',
      });
      fetchProducts(); // 重新获取产品列表
    } catch (error) {
      console.error('产品删除出现异常:', error);
      ElMessage.error(`删除出错: ${error instanceof Error ? error.message : String(error)}`);
    }
  })
  .catch(() => {
    ElMessage({
      type: 'info',
      message: '已取消删除操作',
    });
  });
};

// 监听分页变化
watch([currentPage, pageSize], () => {
  fetchProducts();
});

// 初始化
onMounted(() => {
  fetchProducts();
});
</script>

<style scoped>
  .product-list-container {
    padding: 20px;
  }

  .filter-card {
    margin-bottom: 20px;
  }

  .product-card {
    margin-bottom: 20px;
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .upload-section {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .template-preview-dialog :deep(.el-dialog__body) {
    padding: 20px;
  }

  .field-table-container {
    margin-bottom: 20px;
    overflow-x: auto;
  }

  .field-table {
    width: 100%;
    border-collapse: collapse;
    border: 1px solid #EBEEF5;
  }

  .field-table th, 
  .field-table td {
    padding: 12px;
    text-align: left;
    border: 1px solid #EBEEF5;
  }

  .field-table th {
    background-color: #F5F7FA;
    font-weight: bold;
  }

  .field-table tr:hover {
    background-color: #F5F7FA;
  }

  .required {
    color: #F56C6C;
  }

  .upload-tips h4 {
    margin-top: 0;
  }

  .upload-tips ul {
    padding-left: 20px;
  }

  .upload-tips li {
    margin-bottom: 8px;
  }
  
  /* 新增下载提示样式 */
  :deep(.download-tips) {
    padding: 10px;
    background-color: #f8f9fa;
    border-radius: 4px;
  }
  
  :deep(.download-tips h4) {
    color: #409EFF;
    margin-top: 0;
    margin-bottom: 10px;
  }
  
  :deep(.download-tips ol) {
    padding-left: 20px;
    margin: 0;
  }
  
  :deep(.download-tips li) {
    margin-bottom: 8px;
    line-height: 1.5;
  }
</style>
