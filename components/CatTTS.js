// components/CatTTS.js
"use client";

import { useState } from "react";
import { ElevenLabsProvider, useElevenLabs } from "@elevenlabs/react";

export default function CatTTS() {
  const [text, setText] = useState("");
  const { speak } = useElevenLabs();

  const handleSpeak = async () => {
    if (!text) return;
    await speak({ voice: "XdflFrQO8wbGpWMNZHFr", text });
  };

  return (
    <ElevenLabsProvider apiKey={process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY}>
      <div>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type your text here..."
        />
        <button onClick={handleSpeak}>Speak!</button>
      </div>
    </ElevenLabsProvider>
  );
}
