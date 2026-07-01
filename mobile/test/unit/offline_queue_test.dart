import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/core/storage/offline_queue.dart';

import '../helpers/test_database.dart';

void main() {
  setUpAll(initializeTestDatabase);

  setUp(resetTestDatabase);

  test('supports enqueue and dequeue operations', () async {
    final queue = OfflineQueue();

    final id = await queue.enqueue(
      method: 'POST',
      path: '/messages/conversations',
      body: const {'body': 'Hello'},
    );

    expect(await queue.pendingCount(), 1);
    expect((await queue.getPending()).single.id, id);

    await queue.markCompleted(id);

    expect(await queue.pendingCount(), 0);
  });

  test('increments retry counters for backoff scheduling', () async {
    final queue = OfflineQueue();
    final id = await queue.enqueue(
      method: 'PUT',
      path: '/content/items/content-1',
      body: const {'title': 'Updated'},
    );

    await queue.markFailed(id, 'timeout');
    await queue.resetToPending(id);
    await queue.markFailed(id, 'timeout');

    final failed = await queue.getFailed();

    expect(failed.single.retryCount, 2);
    expect(failed.single.lastError, 'timeout');
  });

  test('preserves explicit idempotency keys and generates missing ones',
      () async {
    final queue = OfflineQueue();

    final explicitId = await queue.enqueue(
      method: 'POST',
      path: '/attendance/class/class-1',
      idempotencyKey: 'custom-key',
    );
    final generatedId = await queue.enqueue(
      method: 'POST',
      path: '/attendance/class/class-2',
    );

    final commands = await queue.getAll();
    final explicit =
        commands.singleWhere((command) => command.id == explicitId);
    final generated =
        commands.singleWhere((command) => command.id == generatedId);

    expect(explicit.idempotencyKey, 'custom-key');
    expect(generated.idempotencyKey, isNotEmpty);
  });
}
