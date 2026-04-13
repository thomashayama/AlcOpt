export function Message({
  message,
}: {
  message: { type: 'success' | 'error'; text: string } | null;
}) {
  if (!message) return null;
  return (
    <p
      role={message.type === 'error' ? 'alert' : 'status'}
      className={
        message.type === 'success'
          ? 'text-sm text-green-500'
          : 'text-sm text-destructive'
      }
    >
      {message.text}
    </p>
  );
}
