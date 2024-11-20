import multiprocessing
from time import sleep

from utils import init_logging

LOG_PATH = "results/multiprocessing/starmap_generator.log"
logger = init_logging(__name__, log_path=LOG_PATH, clear=True)


class MultiProcessingWithArgumentGenerator:
    def __init__(
        self, num_workers: int, argument_generator: callable, process_function: callable
    ):
        self.num_workers = num_workers
        self.argument_generator = argument_generator
        self.process_function = process_function

    def process_completion_callback(self, result):
        logger.info(f"Process with pid {result} completed")
        try:
            next_arg = next(self.arguments)
            self.pool.apply_async(
                self.process_function,
                (next_arg,),
                callback=self.process_completion_callback,
            )
        except StopIteration:
            self.tasks_remaining -= 1

    def run(self):
        logger.info("Start main")
        self.pool = multiprocessing.Pool(self.num_workers)
        self.arguments = self.argument_generator()  # Initialize the argument generator
        self.tasks_remaining = self.num_workers  # Track active tasks

        # Start the initial tasks
        for _ in range(self.num_workers):
            try:
                next_arg = next(self.arguments)
                self.pool.apply_async(
                    self.process_function,
                    (next_arg,),
                    callback=self.process_completion_callback,
                )
            except StopIteration:
                # If there are fewer arguments than workers, adjust task count
                self.tasks_remaining -= 1
                break

        # Wait for all tasks to complete before closing the pool
        while self.tasks_remaining > 0:
            sleep(0.1)  # Sleep briefly to avoid busy-waiting

        self.pool.close()  # Now it's safe to close the pool
        self.pool.join()  # Wait for all tasks to complete

        logger.info("End main")


def single_process(pid):
    process_logger = init_logging(f"pid_{pid}", log_path=LOG_PATH, clear=False)
    process_logger.info(f"Start single process with pid: {pid}")
    sleep(2)  # Simulate processing time
    process_logger.info("End single process")
    return pid


def argument_generator(pids):
    generator_logger = init_logging(
        "argument_generator", LOG_PATH.replace(".log", "2.log"), clear=True
    )
    for i in pids:
        generator_logger.info(f"Yield: {i}")
        yield i


def main():
    multi_processing = MultiProcessingWithArgumentGenerator(
        num_workers=2,
        argument_generator=lambda: argument_generator(range(10)),
        process_function=single_process,
    )
    multi_processing.run()


if __name__ == "__main__":
    main()
