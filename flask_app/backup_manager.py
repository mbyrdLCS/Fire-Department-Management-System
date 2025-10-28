from datetime import datetime
import pytz
import dropbox
import os
import json
import logging
from threading import Timer
import time
from dropbox.exceptions import ApiError, HttpError

class BackupManager:
    def __init__(self, app_key, app_secret, refresh_token, backup_interval=3600, max_retries=3, retry_delay=5):
        self.app_key = app_key
        self.app_secret = app_secret
        self.refresh_token = refresh_token
        self.backup_interval = backup_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timer = None

        # Setup logging
        logging.basicConfig(
            filename='backup.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def get_dropbox_client(self):
        try:
            dbx = dropbox.Dropbox(
                oauth2_refresh_token=self.refresh_token,
                app_key=self.app_key,
                app_secret=self.app_secret,
                timeout=30  # Set a reasonable timeout
            )
            # Verify client works
            dbx.users_get_current_account()
            self.logger.info("Dropbox client initialized successfully")
            return dbx
        except Exception as e:
            self.logger.error(f"Failed to create Dropbox client: {str(e)}")
            raise

    def perform_backup(self, files_to_backup):
        for attempt in range(self.max_retries):
            try:
                dbx = self.get_dropbox_client()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                for local_path, dropbox_base_path in files_to_backup.items():
                    if not os.path.exists(local_path):
                        self.logger.warning(f"File not found for backup: {local_path}")
                        continue

                    with open(local_path, 'rb') as f:
                        file_content = f.read()
                        dropbox_path = f'{dropbox_base_path}_{timestamp}.json'
                        self.logger.info(f"Uploading {local_path} to {dropbox_path}")

                        dbx.files_upload(
                            file_content,
                            dropbox_path,
                            mode=dropbox.files.WriteMode('overwrite')  # Overwrite to avoid conflicts
                        )
                        self.logger.info(f"Successfully backed up {local_path} to {dropbox_path}")

                self._cleanup_old_backups(dbx)
                return True

            except (dropbox.exceptions.AuthError, HttpError) as e:
                self.logger.error(f"Authentication or HTTP error on attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay)
            except Exception as e:
                self.logger.error(f"Backup failed on attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay)

        return False

    def _cleanup_old_backups(self, dbx, keep_last_n=10):
        try:
            result = dbx.files_list_folder('')
            files = [(entry.name, entry.path_display) for entry in result.entries if entry.name.endswith('.json')]

            backup_groups = {}
            for name, path in files:
                backup_type = name.split('_backup_')[0]
                backup_groups.setdefault(backup_type, []).append((name, path))

            for backup_type, backups in backup_groups.items():
                sorted_backups = sorted(backups, key=lambda x: x[0], reverse=True)
                for _, path in sorted_backups[keep_last_n:]:
                    dbx.files_delete_v2(path)
                    self.logger.info(f"Deleted old backup: {path}")

        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")

    def start_automatic_backup(self, files_to_backup):
        def backup_task():
            try:
                self.perform_backup(files_to_backup)
            except Exception as e:
                self.logger.error(f"Automatic backup failed: {str(e)}")
            finally:
                self.timer = Timer(self.backup_interval, backup_task)
                self.timer.start()

        self.timer = Timer(self.backup_interval, backup_task)
        self.timer.start()
        self.logger.info(f"Automatic backup scheduled every {self.backup_interval} seconds")

    def stop_automatic_backup(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None
            self.logger.info("Automatic backup stopped")