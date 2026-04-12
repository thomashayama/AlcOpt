import { redirect } from 'next/navigation';

export default async function ContainerShortcut({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  redirect(`/info?container_id=${id}`);
}
