import argparse
from pathlib import Path
from app.core.config import Settings
from app.inference.classifier import EfficientATClassifier
from app.services.classification import ClassificationService

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("audio",type=Path)
    args=parser.parse_args()
    settings=Settings()
    engine=EfficientATClassifier(settings)
    engine.initialize()
    result=ClassificationService(engine,settings).process(args.audio.read_bytes(),args.audio.name,10,.10)
    print(result.model_dump_json(indent=2))

if __name__=="__main__": main()
