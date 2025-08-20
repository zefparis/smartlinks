/**
 * User History Page
 * View payment history for specific users
 */

import { UserPaymentHistory } from '../../components/finance/UserPaymentHistory';

export function UserHistoryPage() {
  return (
    <div className="p-6">
      <UserPaymentHistory />
    </div>
  );
}
