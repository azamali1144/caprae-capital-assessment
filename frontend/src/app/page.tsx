import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-semibold">LeadLens</h1>
      <p className="text-muted-foreground">Lead intelligence for SaaSquatch exports.</p>
      <Button>Get started</Button>
    </main>
  );
}
