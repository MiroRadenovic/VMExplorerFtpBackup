
class UnexpectedFolderTreeException(Exception):
    """Exception raised for errors in the input.

    Attributes:
        expr -- input expression in which the error occurred
        msg  -- explanation of the error
    """
    def __init__(self, path, exception):
        self.msg = "Cannot create backup from expected folder tree in {0}. error is {1}".format(path, exception)

    def __str__(self):
         return repr(self.msg)
