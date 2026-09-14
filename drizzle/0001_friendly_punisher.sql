CREATE TABLE `beta_accounts` (
	`id` text PRIMARY KEY NOT NULL,
	`email` text NOT NULL,
	`consent` integer DEFAULT 0 NOT NULL,
	`ueno_level` integer DEFAULT 1 NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `beta_activity` (
	`id` text PRIMARY KEY NOT NULL,
	`account_id` text NOT NULL,
	`day` text NOT NULL,
	`kind` text NOT NULL,
	`count` integer DEFAULT 0 NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `beta_activity_owner_day_kind` ON `beta_activity` (`account_id`,`day`,`kind`);--> statement-breakpoint
CREATE TABLE `beta_favorites` (
	`id` text PRIMARY KEY NOT NULL,
	`account_id` text NOT NULL,
	`promo_id` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `beta_favorite_owner_promo` ON `beta_favorites` (`account_id`,`promo_id`);--> statement-breakpoint
CREATE TABLE `beta_reports` (
	`id` text PRIMARY KEY NOT NULL,
	`account_id` text NOT NULL,
	`kind` text NOT NULL,
	`promo_id` text,
	`message` text NOT NULL,
	`version` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
ALTER TABLE `devices` ADD `account_id` text;