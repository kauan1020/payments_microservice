import asyncio
from behave.api.async_step import async_run_until_complete

def before_all(context):
    if not hasattr(context, 'loop'):
        context.loop = asyncio.get_event_loop()

def before_scenario(context, scenario):
    context.error = None
    context.result = None

def after_scenario(context, scenario):
    pass