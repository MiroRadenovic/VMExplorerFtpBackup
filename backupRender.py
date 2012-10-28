
def get_backups_infos(backups):
    if len(backups) == 0:
        return "there are no VM backups to display... "
    else:
        result = ""
        for vmName in backups:
            result += "-[" + vmName + "]\n"
            result += get_backup_dates_and_files_info(backups[vmName])
        return result


def get_backup_dates_and_files_info(backup):
    if len(backup) == 0:
        return "there are no backups to display... "
    result = ""
    for date in backup:
        result += "\t---[" + date.strftime("%Y-%m-%d-%H%M%S") + "]\n"
        for file in backup[date]:
            result += "\t\t--" + file + "\n"
    return result