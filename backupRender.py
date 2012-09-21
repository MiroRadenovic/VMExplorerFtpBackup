
def print_all_backups_infos(backups):
    result = ""
    for vmName in backups:
        result += "-[" + vmName + "]\n"
        result += print_backup_info(backups[vmName])
    return result


def print_backup_info(backup):
    result = ""
    for date in backup:
        result += "\t---[" + date.strftime("%Y-%m-%d-%H%M%S") + "]\n"
        for file in backup[date]:
            result += "\t\t--" + file + "\n"
    return result