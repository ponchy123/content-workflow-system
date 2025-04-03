declare module 'xlsx' {
  export interface Column {
    /** Width in characters */
    wch?: number;
    /** Width in pixels */
    wpx?: number;
  }

  export interface WorkSheet {
    '!cols'?: Column[];
    [key: string]: any;
  }

  export interface WorkBook {
    SheetNames: string[];
    Sheets: { [key: string]: WorkSheet };
  }

  export interface Utils {
    sheet_to_json<T>(
      worksheet: WorkSheet,
      options?: {
        raw?: boolean;
        defval?: any;
        header?: string[] | number;
        range?: any;
      },
    ): T[];
    json_to_sheet<T>(
      data: T[],
      options?: {
        header?: string[];
        skipHeader?: boolean;
      },
    ): WorkSheet;
    aoa_to_sheet(
      data: any[][],
      options?: {
        header?: string[];
        skipHeader?: boolean;
      },
    ): WorkSheet;
    book_new(): WorkBook;
    book_append_sheet(workbook: WorkBook, worksheet: WorkSheet, name?: string): void;
  }

  export const utils: Utils;

  export function read(data: any, options?: { type?: string }): WorkBook;

  export function writeFile(workbook: WorkBook, filename: string): void;
}
