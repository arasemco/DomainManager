import re
import queue
from threading import Thread, Event

import docker

from src.utils.logger import logger
from src.managers.subdomain_manager import SubdomainManager


class DockerEventListener:
    def __init__(self, subdomain_manager: SubdomainManager, base_url: str = 'unix://var/run/docker.sock'):
        logger.debug("Initializing DockerEventListener...")
        self.subdomain_manager = subdomain_manager
        self.docker_client = docker.DockerClient(base_url=base_url)
        self.event_queue = queue.Queue()
        self.stop_event = Event()
        logger.debug("DockerEventListener initialized successfully.")

    def listen(self):
        logger.info("Starting Docker event listener and worker threads...")
        self.stop_event.clear()
        listening_thread = Thread(target=self._event_listener, daemon=True)
        worker_thread = Thread(target=self._process_events, daemon=True)
        listening_thread.start()
        worker_thread.start()
        logger.info("Docker event listener and worker threads started.")

    def _event_listener(self):
        logger.debug("Docker event listener thread started and waiting for events.")
        try:
            for event in self.docker_client.events(decode=True, filters={'type': 'container'}):
                if self.stop_event.is_set():
                    logger.debug("Stop event set. Exiting Docker event listener thread.")
                    break
                logger.debug(f"Event received: {event}")
                self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Error while listening to Docker events: {e}")
        finally:
            logger.info("Docker event listener thread stopped.")

    def _process_events(self):
        logger.debug("Docker event processing thread started.")
        while not self.stop_event.is_set():
            try:
                event = self.event_queue.get(timeout=1)
                if event is not None:
                    logger.debug(f"Processing event: {event}")
                    self._handle_event(event)
                    self.event_queue.task_done()
            except queue.Empty:
                logger.debug("Event queue is empty. Waiting for new events...")
                continue
            except Exception as e:
                logger.error(f"Error while processing Docker event: {e}")
        logger.info("Docker event processing thread stopped.")

    def _handle_event(self, event):
        logger.debug(f"Handling event: {event}")
        action_mapping = {
            'create': self.subdomain_manager.add_subdomain,
            'destroy': self.subdomain_manager.remove_subdomain
        }

        action = event.get('Action')
        labels = event.get('Actor', {}).get('Attributes', {})
        rule_label = labels.get('traefik.http.routers.web.rule', None)

        if rule_label and action in action_mapping:
            match = re.search(r"Host\(`(.+?)`\)", rule_label)
            if match:
                subdomain = match.group(1)
                try:
                    logger.info(f"Executing action '{action}' for subdomain: {subdomain}")
                    action_mapping[action](subdomain)
                    logger.info(f"Action '{action}' completed successfully for subdomain: {subdomain}")
                except Exception as e:
                    logger.error(f"Error while handling event action '{action}' for subdomain '{subdomain}': {e}")
        else:
            logger.debug(f"No matching action found for event: {event}")

    def stop(self):
        logger.info("Stopping DockerEventListener...")
        self.stop_event.set()
        logger.info("DockerEventListener stopped.")
