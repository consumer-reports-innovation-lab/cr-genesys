/*
  Warnings:

  - A unique constraint covering the columns `[device_id]` on the table `sessions` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "sessions_device_id_key" ON "sessions"("device_id");
