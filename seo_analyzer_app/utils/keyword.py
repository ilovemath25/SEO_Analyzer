from ranking_seo import get_keyword
from ranking_seo import load_model
from sentence_transformers import losses
from sentence_transformers import InputExample
from torch.utils.data import DataLoader
from keybert import KeyBERT
import numpy as np
import shutil
import json

def create_train_examples(training_data):
   train_examples = []
   for sentence, keywords in training_data.items():
      for keyword, weight in keywords.items():train_examples.append(InputExample(texts=[sentence, keyword], label=weight))
   return train_examples

def train_model(model, train_examples):
   train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=4)
   train_loss = losses.CosineSimilarityLoss(model)
   model.fit(
      train_objectives=[(train_dataloader, train_loss)],
      epochs=15,
      warmup_steps=200,
      show_progress_bar=True,
      checkpoint_path=None
   )
   temp_model_path = "./seo_analyzer_app/models/temp_fine_tuned_model"
   final_model_path = "./seo_analyzer_app/models/fine_tuned_seo_model"
   model.save(temp_model_path)
   shutil.rmtree(final_model_path, ignore_errors=True)
   shutil.move(temp_model_path, final_model_path)

def test_model(training_data, model):
   for sentence, expected_keywords in training_data.items():
      print("Sentence           :", sentence)
      extracted_keywords = get_keyword(sentence, model, 30)
      normalized_extracted = dict(sorted(
         {kw.lower().replace("-", " ").strip(): score for kw, score in extracted_keywords.items()}.items(),
         key=lambda x: x[1], reverse=True)[:10])
      normalized_expected = dict(sorted(
         {kw.lower().replace("-", " ").strip(): score for kw, score in expected_keywords.items()}.items(),
         key=lambda x: x[1], reverse=True)[:10])
      mse_loss = []
      weighted_accuracy_sum = 0
      total_keywords = len(normalized_expected)
      for kw, score in normalized_extracted.items():
         best_match = None
         best_score_diff = float("inf")
         for expected_kw, expected_score in normalized_expected.items():
            if expected_kw in kw or kw in expected_kw:
               score_diff = abs(score - expected_score)
               if score_diff < best_score_diff:
                  best_score_diff = score_diff
                  best_match = expected_kw
         if best_match:
            mse_loss.append(best_score_diff ** 2)
            keyword_accuracy = max(0, 1 - best_score_diff)
            weighted_accuracy_sum += keyword_accuracy
         else:
            mse_loss.append(score ** 2)  
            weighted_accuracy_sum += 0
      weighted_accuracy = weighted_accuracy_sum / total_keywords if total_keywords else 0.0
      loss = np.mean(mse_loss) if mse_loss else 0.0
      print("Comparison Table   :")
      print(f"{'Keyword':<40}{'Expected Value':<20}{'Extracted Value':<20}{'Difference':<20}{'Accuracy (Per Keyword)'}")
      print("-" * 120)
      for kw in normalized_expected:
         expected_value = normalized_expected[kw]
         extracted_value = max(
            [normalized_extracted.get(e_kw, 0) for e_kw in normalized_extracted if kw in e_kw or e_kw in kw],
            default=0
         )
         difference = abs(extracted_value - expected_value)
         keyword_accuracy = max(0, 1 - difference)
         print(f"{kw:<40}{expected_value:<20}{extracted_value:<20}{difference:<20.4f}{keyword_accuracy:<20.4f}")
      print("Weighted Accuracy  : {:.4f}%".format(weighted_accuracy*100))
      print("Loss (MSE)         : {:.4f}%".format(loss*100))
      print("=" * 120)

if __name__ == "__main__":
   with open("./seo_analyzer_app/utils/training_data.json", "r") as f: training_data = json.load(f)
   model = load_model("./seo_analyzer_app/models/fine_tuned_seo_model")
   kw_model = KeyBERT(model)
   train_examples = create_train_examples(training_data)
   
   # train_model(model, train_examples)
   
   test_model(training_data, kw_model)