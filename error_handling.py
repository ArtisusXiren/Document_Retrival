import logging
logging.basicConfig(
    filename='error_log.comfig',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
def handle_error(error):
    logging.error("An error has occurred : %s",error,exc_info=True)
  
    