import time
import uuid
import numpy as np
from app.api.schemas import AudioInfo, ClassificationResponse, ModelInfo, Prediction, Segment
from app.audio.decoder import SAMPLE_RATE, decode_audio
from app.audio.preprocessing import segment_audio
from app.audio.validation import check_upload
from app.core.config import RELEASE, Settings

class ClassificationService:
    def __init__(self,engine,settings: Settings):
        self.engine=engine; self.settings=settings

    def process(self,data: bytes,filename: str,top_k: int,threshold: float):
        began=time.perf_counter()
        check_upload(data,filename,self.settings.max_upload_mb*1024*1024)
        audio=decode_audio(data,max_duration=self.settings.max_duration_seconds,
                            max_decode_bytes=self.settings.max_decode_bytes)
        segments=[]; score_rows=[]
        for start,end,samples in segment_audio(audio,self.settings.window_seconds):
            scores=self.engine.predict(samples)
            if len(scores)!=527: raise RuntimeError("Model must return 527 scores")
            score_rows.append(scores)
            segments.append(Segment(start_seconds=round(start,4),end_seconds=round(end,4),
                                    predictions=self._top(scores,top_k,threshold)))
        clip_scores=np.asarray(score_rows,dtype=np.float32).mean(axis=0).tolist()
        preds=self._top(clip_scores,top_k,threshold)
        return ClassificationResponse(request_id=uuid.uuid4().hex,
               model=ModelInfo(id=self.settings.model_name,release=RELEASE),
               audio=AudioInfo(filename=filename,duration_seconds=round(len(audio)/SAMPLE_RATE,4),
                               windows=len(segments)),predictions=preds,segments=segments,
               processing_time_ms=round((time.perf_counter()-began)*1000,2),
               warnings=[] if preds else ["no_event_above_threshold"])

    def _top(self,scores,top_k,threshold):
        indices=sorted(range(len(scores)),key=lambda i:float(scores[i]),reverse=True)
        return [Prediction(label_id=i,label=self.engine.labels[i],score=round(float(scores[i]),5))
                for i in indices if float(scores[i])>=threshold][:top_k]
