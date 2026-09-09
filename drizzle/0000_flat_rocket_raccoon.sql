CREATE TABLE `deliveries` (
	`key` text PRIMARY KEY NOT NULL,
	`status` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `devices` (
	`id` text PRIMARY KEY NOT NULL,
	`token_hash` text NOT NULL,
	`subscription` text NOT NULL,
	`favorites` text NOT NULL,
	`ueno_level` integer DEFAULT 1 NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `devices_token_hash_unique` ON `devices` (`token_hash`);