import time

from .azure_worker import AzureRenderWorker


def main() -> None:
    worker = AzureRenderWorker.from_environment()
    while True:
        if not worker.run_once():
            time.sleep(2)


if __name__ == "__main__":
    main()
