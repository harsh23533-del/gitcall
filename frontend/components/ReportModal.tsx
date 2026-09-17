import { useState } from "react";

const REASONS = [
  { value: "harassment", label: "Harassment" },
  { value: "inappropriate_content", label: "Inappropriate content" },
  { value: "spam", label: "Spam" },
  { value: "other", label: "Other" },
];

export default function ReportModal({
  onSubmit,
  onClose,
}: {
  onSubmit: (reason: string, details: string) => void;
  onClose: () => void;
}) {
  const [reason, setReason] = useState(REASONS[0].value);
  const [details, setDetails] = useState("");

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-white text-black rounded-lg p-6 w-full max-w-sm space-y-4">
        <h2 className="text-lg font-semibold">Report this user</h2>

        <label className="block text-sm">
          Reason
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="mt-1 w-full border rounded-md px-3 py-2"
          >
            {REASONS.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          Details (optional)
          <textarea
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            rows={3}
            className="mt-1 w-full border rounded-md px-3 py-2"
          />
        </label>

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 rounded-md text-sm hover:bg-gray-100">
            Cancel
          </button>
          <button
            onClick={() => onSubmit(reason, details)}
            className="px-4 py-2 rounded-md bg-red-600 text-white text-sm hover:bg-red-500"
          >
            Submit report
          </button>
        </div>
      </div>
    </div>
  );
}
