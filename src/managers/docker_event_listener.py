import re
import time
import queue
from threading import Thread

import docker

from src.utils.logger import logger
from src.managers.subdomain_manager import SubdomainManager


class DockerEventListener:
    def __init__(self, subdomain_manager: SubdomainManager, base_url: str = 'unix://var/run/docker.sock'):
        self.subdomain_manager = subdomain_manager
        self.docker_client = docker.DockerClient(base_url=base_url)
        self.event_queue = queue.Queue()

    def listen(self):
        listening_thread = Thread(target=self._event_listener, daemon=True)
        worker_thread = Thread(target=self._process_events, daemon=True)
        listening_thread.start()
        worker_thread.start()

    def _event_listener(self):
        try:
            for event in self.docker_client.events(decode=True, filters={'type': 'container'}):
                self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Error while listening to Docker events: {e}")

    def _process_events(self):
        while True:
            event = self.event_queue.get()
            if event is not None:
                self._handle_event(event)
                self.event_queue.task_done()
                continue

            self.event_queue.task_done()
            time.sleep(1)

    def _handle_event(self, event):
        action_mapping = {
            'create': self.subdomain_manager.add_subdomain,
            'destroy': self.subdomain_manager.remove_subdomain
        }

        action = event['Action']
        labels = event['Actor']['Attributes']
        rule_label = labels.get('traefik.http.routers.web.rule', None)

        if rule_label and action in action_mapping:
            match = re.search(r"Host\(`(.+?)`\)", rule_label)
            if match:
                action_mapping[action](match.group(1))
