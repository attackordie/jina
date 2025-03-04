from typing import Optional

from docarray import Document, DocumentArray
from pydantic import BaseModel
from uvicorn import Config, Server

from jina import Gateway, __default_host__
from jina.clients.request import request_generator


class DummyResponseModel(BaseModel):
    arg1: Optional[str]
    arg2: Optional[str]
    arg3: Optional[str]


class ProcessedResponseModel(BaseModel):
    text: str
    tags: Optional[dict]


class DummyGateway(Gateway):
    def __init__(
        self,
        port: int = None,
        arg1: str = None,
        arg2: str = None,
        arg3: str = 'default-arg3',
        **kwargs
    ):
        super().__init__(**kwargs)
        self.port = port
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3

    async def setup_server(self):
        from fastapi import FastAPI

        app = FastAPI(
            title='Dummy Server',
        )

        @app.get(path='/', response_model=DummyResponseModel)
        def _get_response():
            return {
                'arg1': self.arg1,
                'arg2': self.arg2,
                'arg3': self.arg3,
            }

        @app.get(
            path='/stream',
            response_model=ProcessedResponseModel,
        )
        async def _process(text: str):
            doc = None
            async for req in self.streamer.stream(
                request_generator(
                    exec_endpoint='/',
                    data=DocumentArray([Document(text=text)]),
                )
            ):
                doc = req.to_dict()['data'][0]
            return {'text': doc['text'], 'tags': doc['tags']}

        self.server = Server(Config(app, host=__default_host__, port=self.port))

    async def run_server(self):
        await self.server.serve()

    async def teardown(self):
        await super().teardown()
        await self.server.shutdown()

    async def stop_server(self):
        self.server.should_exit = True

    @property
    def should_exit(self) -> bool:
        return self.server.should_exit
