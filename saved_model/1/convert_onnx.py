import joblib
import onnxmltools
from onnxmltools.convert.common.data_types import FloatTensorType

# Charger le modèle LightGBM
model = joblib.load(r'C:\Users\pothfred\Documents\T-S\Python\Projets\projet_corrige (1)\saved_model\1\model_lgbm_fb090954.joblib')

# Définir les 74 features identifiées
initial_types = [['float_input', FloatTensorType([None, 75])]]

# Conversion en ONNX avec zipmap=False passé directement
onnx_model = onnxmltools.convert_lightgbm(
    model, 
    initial_types=initial_types, 
    target_opset=12, 
    zipmap=False  # C'est ici que s'effectue la correction
)

onnxmltools.utils.save_model(onnx_model, r'C:\Users\pothfred\Documents\T-S\Python\Projets\projet_corrige (1)\saved_model\1\model.onnx')