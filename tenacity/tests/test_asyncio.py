# coding: utf-8
# Copyright 2016 Étienne Bersac
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import pytest
from tenacity import RetryError
from tenacity import _asyncio as tasyncio
from tenacity import retry, stop_after_attempt
from tenacity.tests.test_tenacity import NoIOErrorAfterCount


@retry
async def _retryable_coroutine(thing):
    await asyncio.sleep(0.00001)
    return thing.go()


@retry(stop=stop_after_attempt(2))
async def _retryable_coroutine_with_2_attempts(thing):
    await asyncio.sleep(0.00001)
    thing.go()



@pytest.mark.asyncio
async def test_retry():
    assert asyncio.iscoroutinefunction(_retryable_coroutine)
    thing = NoIOErrorAfterCount(5)
    await _retryable_coroutine(thing)
    assert thing.counter == thing.count


@pytest.mark.asyncio
async def test_stop_after_attempt():
    assert asyncio.iscoroutinefunction(
        _retryable_coroutine_with_2_attempts)
    thing = NoIOErrorAfterCount(2)
    try:
        await _retryable_coroutine_with_2_attempts(thing)
    except RetryError:
        assert thing.counter == 2

def test_repr():
    repr(tasyncio.AsyncRetrying())


@pytest.mark.asyncio
async def test_attempt_number_is_correct_for_interleaved_coroutines():
    attempts = []

    def after(retry_state):
        attempts.append((retry_state.args[0], retry_state.attempt_number))

    thing1 = NoIOErrorAfterCount(3)
    thing2 = NoIOErrorAfterCount(3)
    future1 = asyncio.ensure_future(
        _retryable_coroutine.retry_with(after=after)(thing1))
    future2 = asyncio.ensure_future(
        _retryable_coroutine.retry_with(after=after)(thing2))
    await asyncio.gather(future1, future2)

    # There's no waiting on retry, only a wait in the coroutine, so the
    # executions should be interleaved.
    thing1_attempts = attempts[::2]
    things1, attempt_nos1 = zip(*thing1_attempts)
    assert all(thing is thing1 for thing in things1)
    assert list(attempt_nos1) == [1, 2, 3]

    thing2_attempts = attempts[1::2]
    things2, attempt_nos2 = zip(*thing2_attempts)
    assert all(thing is thing2 for thing in things2)
    assert list(attempt_nos2) == [1, 2, 3]
