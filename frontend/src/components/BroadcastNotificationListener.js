import { useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';
const POLL_INTERVAL = 30000; // Check every 30 seconds

/**
 * Hook to monitor for new critical/high priority broadcasts
 * Shows toast notifications when new urgent broadcasts are detected
 */
export function useBroadcastNotifications() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const lastCheckRef = useRef(new Date().toISOString());
  const seenBroadcastsRef = useRef(new Set());
  const intervalRef = useRef(null);

  const checkForNewBroadcasts = useCallback(async () => {
    if (!user || !token) return;

    try {
      const response = await fetch(`${API_URL}/broadcasts/active`);
      if (!response.ok) return;

      const data = await response.json();
      const broadcasts = data.broadcasts || [];

      // Filter for critical and high priority broadcasts from OTHER organizations
      const importantBroadcasts = broadcasts.filter(b => 
        (b.priority === 'critical' || b.priority === 'high') &&
        b.org_id !== user.org_id &&
        !seenBroadcastsRef.current.has(b.id)
      );

      // Check for new broadcasts (created after last check)
      const newBroadcasts = importantBroadcasts.filter(b => {
        const createdAt = new Date(b.created_at);
        const lastCheck = new Date(lastCheckRef.current);
        return createdAt > lastCheck;
      });

      // Show notifications for new broadcasts
      newBroadcasts.forEach(broadcast => {
        seenBroadcastsRef.current.add(broadcast.id);
        
        const isCritical = broadcast.priority === 'critical';
        const icon = isCritical ? '🚨' : '⚠️';
        const title = `${icon} ${isCritical ? 'Critical' : 'Urgent'}: ${broadcast.blood_group} Blood Needed`;
        
        toast(title, {
          description: `${broadcast.org_name}: ${broadcast.title}`,
          duration: isCritical ? 15000 : 10000, // Critical stays longer
          action: {
            label: 'View',
            onClick: () => navigate('/broadcasts')
          },
          style: {
            background: isCritical ? '#fef2f2' : '#fffbeb',
            border: isCritical ? '1px solid #fecaca' : '1px solid #fde68a',
          }
        });
      });

      // Update last check time
      lastCheckRef.current = new Date().toISOString();

      // Also mark all current important broadcasts as seen (for initial load)
      importantBroadcasts.forEach(b => seenBroadcastsRef.current.add(b.id));

    } catch (error) {
      console.error('Failed to check broadcasts:', error);
    }
  }, [user, token, navigate]);

  useEffect(() => {
    if (!user || !token) return;

    // Initial check after a short delay (let the app settle)
    const initialTimeout = setTimeout(() => {
      checkForNewBroadcasts();
    }, 3000);

    // Set up polling interval
    intervalRef.current = setInterval(checkForNewBroadcasts, POLL_INTERVAL);

    return () => {
      clearTimeout(initialTimeout);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [user, token, checkForNewBroadcasts]);

  return null;
}

/**
 * Component wrapper for the hook - to be used in Layout
 */
export default function BroadcastNotificationListener() {
  useBroadcastNotifications();
  return null;
}
