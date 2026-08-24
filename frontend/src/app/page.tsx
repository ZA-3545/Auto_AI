"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { AssistantExperience } from "@/components/assistant-experience";

function HomeWithPrompt() {
  const searchParams = useSearchParams();
  const [prompt, setPrompt] = useState("");

  useEffect(() => {
    const q = searchParams.get("q") ?? searchParams.get("prompt") ?? "";
    setPrompt(q);
  }, [searchParams]);

  return <AssistantExperience initialPrompt={prompt} />;
}

export default function HomePage() {
  return (
    <Suspense fallback={<AssistantExperience />}>
      <HomeWithPrompt />
    </Suspense>
  );
}
