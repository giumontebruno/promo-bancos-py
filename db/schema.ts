import { sqliteTable, text, integer, uniqueIndex } from 'drizzle-orm/sqlite-core';

export const devices = sqliteTable('devices', {
  id: text('id').primaryKey(),
  tokenHash: text('token_hash').notNull(),
  subscription: text('subscription').notNull(),
  favorites: text('favorites').notNull(),
  uenoLevel: integer('ueno_level').notNull().default(1),
  updatedAt: text('updated_at').notNull(),
  accountId: text('account_id'),
}, table => [uniqueIndex('devices_token_hash_unique').on(table.tokenHash)]);

export const deliveries = sqliteTable('deliveries', {
  key: text('key').primaryKey(),
  status: text('status').notNull(),
  createdAt: text('created_at').notNull(),
});

export const serviceErrors = sqliteTable('service_errors', {
  id: text('id').primaryKey(), area: text('area').notNull(), code: text('code').notNull(), createdAt: text('created_at').notNull(),
});

export const betaAccounts = sqliteTable('beta_accounts', {
  id: text('id').primaryKey(), email: text('email').notNull(),
  consent: integer('consent').notNull().default(0),
  uenoLevel: integer('ueno_level').notNull().default(1),
  createdAt: text('created_at').notNull(),
});
export const betaFavorites = sqliteTable('beta_favorites', {
  id: text('id').primaryKey(), accountId: text('account_id').notNull(), promoId: text('promo_id').notNull(),
}, t => [uniqueIndex('beta_favorite_owner_promo').on(t.accountId, t.promoId)]);
export const betaActivity = sqliteTable('beta_activity', {
  id: text('id').primaryKey(), accountId: text('account_id').notNull(), day: text('day').notNull(),
  kind: text('kind').notNull(), count: integer('count').notNull().default(0),
}, t => [uniqueIndex('beta_activity_owner_day_kind').on(t.accountId, t.day, t.kind)]);
export const betaReports = sqliteTable('beta_reports', {
  id: text('id').primaryKey(), accountId: text('account_id').notNull(),
  kind: text('kind').notNull(), promoId: text('promo_id'), message: text('message').notNull(),
  version: text('version').notNull(), createdAt: text('created_at').notNull(),
});
