/**
 * A phone line is shown as sent only after the server has accepted it.
 * Until then it stays pending. A timeout or an error is a visible failure
 * the player can retry with the same id (the server will not apply it twice).
 */
export type LineDelivery = 'pending' | 'sent' | 'failed';

export type DeliveryEvent = 'ack' | 'echo' | 'error' | 'timeout';

export function deliveryAfterServer(status: LineDelivery, event: DeliveryEvent): LineDelivery {
  if (event === 'ack' || event === 'echo') return 'sent';
  if (event === 'error') return 'failed';
  // A late timeout must not un-send a line the server already accepted.
  if (status === 'sent') return 'sent';
  return 'failed';
}

/** Shown in the feed as a normal sent action — history rows have no status. */
export function shownAsSent(status: LineDelivery | undefined): boolean {
  return status === undefined || status === 'sent';
}
