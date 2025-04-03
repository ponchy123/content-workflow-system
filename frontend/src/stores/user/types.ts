import type { UserInfo } from '@/types/user';

export interface UserState {
  token: string;
  refreshToken: string;
  tokenExpireTime: number;
  userInfo: UserInfo | null;
  isRefreshing: boolean;
}

export interface UserGetters {
  isLoggedIn: boolean;
  isTokenExpiring: boolean;
  permissions: string[];
  roles: string[];
  isAdmin: boolean;
}

export interface UserActions {
  loginAction: (username: string, password: string) => Promise<UserInfo>;
  logout: () => Promise<void>;
  initialize: () => Promise<void>;
  refreshUserInfo: () => Promise<UserInfo>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  refreshTokenHandler: () => Promise<string>;
} 