"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { PublicLesson } from "@/lib/types";

type SavedProgress = { position: number; completed: boolean };
const storageKey = (id: string) => `french-listening:v1:${id}`;

function useProgress(lessonId: string) {
  const [progress, setProgress] = useState<SavedProgress>({ position: 0, completed: false });
  useEffect(() => {
    try { const value = localStorage.getItem(storageKey(lessonId)); if (value) setProgress(JSON.parse(value)); } catch { /* Ignore unavailable or corrupt browser storage. */ }
  }, [lessonId]);
  const save = (update: Partial<SavedProgress>) => setProgress((current) => {
    const next = { ...current, ...update };
    try { localStorage.setItem(storageKey(lessonId), JSON.stringify(next)); } catch { /* Progress is an enhancement, never a blocker. */ }
    return next;
  });
  return [progress, save] as const;
}

function AudioPlayer({ lessonId, startAt, onPosition }: { lessonId: string; startAt: number; onPosition: (position: number) => void }) {
  const audio = useRef<HTMLAudioElement>(null);
  useEffect(() => { if (audio.current && startAt > 0) audio.current.currentTime = startAt; }, [startAt]);
  return <audio ref={audio} controls preload="metadata" className="audio" src={`/api/lessons/${encodeURIComponent(lessonId)}/audio`} onTimeUpdate={(event) => onPosition(Math.floor(event.currentTarget.currentTime))}>Votre navigateur ne prend pas en charge l’audio.</audio>;
}

function Quiz({ lesson, done }: { lesson: PublicLesson; done: () => void }) {
  const [choice, setChoice] = useState<number | null>(null); const [result, setResult] = useState<{ correct: boolean; optionRationale: string; explanation: string } | null>(null); const [sending, setSending] = useState(false);
  async function submit() { if (choice === null) return; setSending(true); const response = await fetch(`/api/lessons/${encodeURIComponent(lesson.lessonId)}/attempt`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ optionIndex: choice }) }); const value = await response.json(); setSending(false); if (response.ok) { setResult(value); done(); } }
  return <section className="exercise"><p className="eyebrow">APRÈS L’ÉCOUTE</p><h2>{lesson.question}</h2><div className="options">{lesson.options?.map((option, index) => <label className={`option ${choice === index ? "selected" : ""}`} key={option}><input type="radio" name="quiz" checked={choice === index} disabled={!!result} onChange={() => setChoice(index)} /><span>{option}</span></label>)}</div>{!result ? <button className="button" disabled={choice === null || sending} onClick={submit}>{sending ? "Vérification…" : "Vérifier ma réponse"}</button> : <div className={`feedback ${result.correct ? "correct" : "incorrect"}`}><strong>{result.correct ? "Bonne réponse." : "Pas tout à fait."}</strong><p>{result.optionRationale}</p><p>{result.explanation}</p></div>}</section>;
}

function Blanks({ lesson, done }: { lesson: PublicLesson; done: () => void }) {
  const [answers, setAnswers] = useState<Record<number, string>>({}); const [result, setResult] = useState<{ results: Array<{ index: number; correct: boolean; answer: string; hint?: string }>; correctCount: number; total: number } | null>(null); const [sending, setSending] = useState(false);
  const feedback = (index: number) => result?.results.find((item) => item.index === index);
  async function submit() { setSending(true); const response = await fetch(`/api/lessons/${encodeURIComponent(lesson.lessonId)}/attempt`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ answers }) }); const value = await response.json(); setSending(false); if (response.ok) { setResult(value); done(); } }
  return <section className="exercise"><p className="eyebrow">PENDANT L’ÉCOUTE</p><h2>Complétez le texte</h2><p className="exercise-intro">Écoutez puis écrivez les mots manquants. Les indices apparaissent après la correction.</p><div className="passage">{lesson.passageSegments?.map((segment, position) => segment.type === "text" ? <span key={position}>{segment.value}</span> : (() => { const item = feedback(segment.index); return <span className="blank-wrap" key={position}><input aria-label={`Réponse ${segment.index}`} value={answers[segment.index] ?? ""} disabled={!!result} onChange={(event) => setAnswers((current) => ({ ...current, [segment.index]: event.target.value }))} className={item ? (item.correct ? "blank correct" : "blank incorrect") : "blank"} /><sup>{segment.index}</sup>{item && !item.correct && <small>Réponse : {item.answer}{item.hint ? ` · ${item.hint}` : ""}</small>}</span>; })())}</div>{!result ? <button className="button" disabled={sending} onClick={submit}>{sending ? "Vérification…" : "Vérifier mes réponses"}</button> : <div className="feedback correct"><strong>{result.correctCount} / {result.total} réponses correctes</strong><p>Vous pouvez réécouter la leçon puis recommencer avec une nouvelle leçon.</p></div>}</section>;
}

export function LessonExperience({ lesson }: { lesson: PublicLesson }) {
  const [progress, save] = useProgress(lesson.lessonId);
  const minutes = lesson.durationSec ? `${Math.round(lesson.durationSec / 60)} min` : "Leçon audio";
  return <section className="lesson-page"><Link className="back" href="/">← Toutes les leçons</Link><div className="lesson-heading"><p className="eyebrow">{lesson.workflow === "quiz" ? "QUIZ D’ÉCOUTE" : "TEXTE À COMPLÉTER"} · {lesson.difficulty}</p><h1>{lesson.titleFr}</h1><p>{lesson.summaryEn}</p><div className="lesson-details"><span>{minutes}</span><span>{lesson.wordCount} mots</span>{progress.completed && <span className="completed">Terminée</span>}</div></div><AudioPlayer lessonId={lesson.lessonId} startAt={progress.position} onPosition={(position) => save({ position })} />{lesson.workflow === "quiz" ? <><Quiz lesson={lesson} done={() => save({ completed: true })} /><section className="transcript"><h2>Transcription</h2><p>{lesson.script}</p></section></> : <Blanks lesson={lesson} done={() => save({ completed: true })} />}<aside className="resources"><div><h2>Vocabulaire</h2>{lesson.glossary.length ? <dl>{lesson.glossary.map((term) => <div key={term.term}><dt>{term.term}</dt><dd>{term.definition}{term.translationEn ? ` — ${term.translationEn}` : ""}</dd></div>)}</dl> : <p>Pas de glossaire pour cette leçon.</p>}</div><div><h2>Sources</h2><ul>{lesson.sources.map((source) => <li key={source.url}><a href={source.url} target="_blank" rel="noreferrer">{source.title || source.origin || source.url}</a></li>)}</ul></div></aside></section>;
}
