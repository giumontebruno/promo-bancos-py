import { sqliteTable, text, integer, uniqueIndex } from 'drizzle-orm/sqlite-core';

export const devices = sqliteTable('devices', {
  id: text('id').primaryKey(),
  tokenHash: text('token_hash').notNull(),
  subscription: text('subscription').notNull(),
  favorites: text('favorites').notNull(),
  uenoLevel: integer('ueno_level').notNull().default(1),
  updatedAt: text('updated_at').notNull(),
}, table => [uniqueIndex('devices_token_hash_unique').on(table.tokenHash)]);

export const deliveries = sqliteTable('deliveries', {
  key: text('key').primaryKey(),
  status: text('status').notNull(),
  createdAt: text('created_at').notNull(),
});
