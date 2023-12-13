import queue
from queue import Queue
from typing import Union
from scrapy.http.request import Request
from threading import Lock
try:
    from scrapy.utils.request import request_from_dict
except ImportError:
    from scrapy.utils.reqser import request_to_dict, request_from_dict

mutex = Lock()


class RequestQueue:

    def __init__(self, spider, mode: str):
        self.wait_queue = Queue()
        self.wait_ack_queue = {}
        self.spider = spider

    def pop(self, block_pop_timeout: int) -> Union[None, Request]:
        try:
            req = self.wait_queue.get(timeout=block_pop_timeout)
        except queue.Empty as e:
            return None
        if req:
            req_id = req.get("meta", {}).get("req_id")
            if self.spider.settings['MODE'] not in ['STRICT']:
                mutex.acquire(2)
                self.wait_ack_queue.pop(req_id)
                mutex.release()
                return request_from_dict(d=req, spider=self.spider)

            if self.wait_ack_queue.get(req_id) == 1:
                # ack
                mutex.acquire(2)
                self.wait_ack_queue.pop(req_id)
                mutex.release()
                return request_from_dict(d=req, spider=self.spider)

            elif self.wait_ack_queue.get(req_id) == -1:
                # fail
                mutex.acquire(2)
                self.wait_ack_queue.pop(req_id)
                mutex.release()
                return None

            elif self.wait_ack_queue.get(req_id) == 0:
                # wait
                self.wait_queue.put(req)
                return None
            elif self.wait_ack_queue.get(req_id) == 2:
                # end-wait
                self.wait_queue.put(req)
                return None
            else:
                print("发生未知错误！")

        else:
            return None

    def push(self, request: Request):
        req_id = request.meta.get("req_id")
        mutex.acquire(2)
        if request.meta.get('is_retry') or request.meta.get('is_begin'):
            self.wait_ack_queue[req_id] = 1
        else:
            self.wait_ack_queue[req_id] = 0
        mutex.release()
        self.wait_queue.put(request.to_dict(spider=self.spider))

    def ack(self, req_id):
        mutex.acquire(2)
        _status = self.wait_ack_queue.get(req_id)
        if _status == 0:
            self.wait_ack_queue[req_id] = 1
        # elif _status == 2:
        #     self.wait_ack_queue[req_id] = 3
        mutex.release()

    def nack(self, req_id):
        mutex.acquire(2)
        self.wait_ack_queue[req_id] = -1
        mutex.release()


    def replay(self, request: Request):
        pass


    # def tack(self, req_id):
    #     mutex.acquire(2)
    #     self.wait_ack_queue[req_id] = 2
    #     mutex.release()


    def __len__(self):
        return self.wait_queue.qsize()
