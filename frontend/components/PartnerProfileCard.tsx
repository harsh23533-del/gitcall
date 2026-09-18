import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PartnerProfile {
  id: number;
  username: string;
  avatar_url: string | null;
  bio: string | null;
  top_languages: string[] | null;
}

export default function PartnerProfileCard({ userId }: { userId: number | null }) {
  const [profile, setProfile] = useState<PartnerProfile | null>(null);

  useEffect(() => {
    if (!userId) return;
    let cancelled = false;

    fetch(`${API_URL}/users/${userId}`)
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled) setProfile(data);
      })
      .catch(() => {
        if (!cancelled) setProfile(null);
      });

    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (!profile) return null;

  return (
    <div className="flex items-center gap-3 bg-black/60 rounded-lg px-3 py-2 text-sm">
      {profile.avatar_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={profile.avatar_url} alt={profile.username} className="w-9 h-9 rounded-full" />
      )}
      <div>
        <div className="font-medium">{profile.username}</div>
        {profile.top_languages && profile.top_languages.length > 0 && (
          <div className="text-xs text-gray-400">{profile.top_languages.join(" · ")}</div>
        )}
      </div>
    </div>
  );
}
