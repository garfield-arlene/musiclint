import logging

class logIT:
    def __init__(self,log_location):
        self.log_location = log_location

    def write(self,message=None):

        logging.basicConfig(
            filename=self.log_location,
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p'
        )
        if message == None:
            logging.info(
                "******************** Start processing ********************"
            )
        else:
            logging.info(str(message))


