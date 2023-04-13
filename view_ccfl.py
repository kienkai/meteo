import os

import streamlit as st
import csv
from typing import  List, Tuple, Dict, Any
from google.cloud import vision_v1
from google.cloud.vision_v1 import AnnotateImageResponse
from google.oauth2 import service_account

#from commons.api.googlevision import GoogleVisionOcr
#from commons.constants import DOCUMENT_TEXT_DETECTION, TEXT_DETECTION
#from commons.utils.prepare_text_from_db import extract_full_text_from_ocr_objects

TEXT_DETECTION = 0
DOCUMENT_TEXT_DETECTION = 1

class GoogleVisionOcr:
    def __init__(self):
        """connect to google vision

        Returns
        -------
        client object
            client object returned by google vision
        """
        #creds = service_account.Credentials.from_service_account_file("GoogleVision.json")

        service_account_info = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"]
        }

        creds = service_account.Credentials.from_service_account_info(service_account_info)

        self.client = vision_v1.ImageAnnotatorClient(credentials=creds)

    def get_google_vision_text(self, img, type):
        """[summary]

        Parameters
        ----------
        img : [type]
            [description]
        creds : [type]
            [description]
        client : [type]
            [description]

        Returns
        -------
        [type]
            [description]
        """

        response = self.get_google_vision_all(img, type)
        text = response.text_annotations

        if text:
            return text[0].description
        else:
            return ""

    def get_google_vision_all(self, img, type):
        """[summary]

        Parameters
        ----------
        img : image object

        type : string
            A string variable that can take only two values : text_detection or document_text_detection
        client : credentials account
            credentials account that enable to access vision functionnality
        """

        if type == TEXT_DETECTION:
            # response = self.client.annotate_image({'image': {'content': img},'features': [{'type_': vision_v1.Feature.Type.TEXT_DETECTION,'model': "builtin/legacy"}]})
            response = self.client.annotate_image(
                {"image": {"content": img}, "features": [{"type_": vision_v1.Feature.Type.TEXT_DETECTION}]}
            )
        elif type == DOCUMENT_TEXT_DETECTION:
            # response = self.client.annotate_image({'image': {'content': img},'features': [{'type_': vision_v1.Feature.Type.DOCUMENT_TEXT_DETECTION,'model': "builtin/legacy"}]})
            response = self.client.annotate_image(
                {"image": {"content": img}, "features": [{"type_": vision_v1.Feature.Type.DOCUMENT_TEXT_DETECTION}]}
            )
        else:
            return ""

        return response

    def structure_google_vision_return(self, img, type):
        """[summary]

        Parameters
        ----------
        img : image object

        type : string
            A string variable that can take only two values : text_detection or document_text_detection


        Returns
        -------
        res : a dictionnary composed of a two great dictionnaries
        global : account for the whole text and composed of a
                    text : the whole text
                    polygon : a list of points that compose the polygon bording the whole text
        words : a list of words
        serialized_proto_plus : a binary serializer containing the whole answer from googlevision
        """
        response = self.get_google_vision_all(img, type)

        # serialize / deserialize proto (binary)
        serialized_proto_plus = AnnotateImageResponse.serialize(response)

        text = response.text_annotations
        if text:
            global_val = {"text": text[0].description, "polygon": list()}
            words_val = []
            for val in text[1:]:
                tmp = {"text": val.description, "polygon": list()}
                words_val.append(tmp)

            res = {"global": global_val, "words": words_val}
            return res, serialized_proto_plus
        else:
            return {}, serialized_proto_plus

def extract_full_text_from_ocr_object(ocr_json: Dict[str, Any]) -> str:
    """extract data from images readed with googlevision
    """
    raw_text = ""
    if ocr_json:
        for ocr_content in ocr_json.values():
            if ocr_content:
                raw_text += ocr_content["global"]["text"] + "\n"
    return raw_text

def extract_full_text_from_ocr_objects(ocr_jsons: List[Dict[str, Any]]) -> str:
    raw_text = ""
    for ocr_json in ocr_jsons:
        raw_text = raw_text + extract_full_text_from_ocr_object(ocr_json)
    return raw_text


# connexion to google vision OCR
google_vision_ocr = GoogleVisionOcr()

def sel_brand():
    brand_names = ['no brand','sony','dell']
    #brand_names = sorted(brand_names)
    brand_name = st.sidebar.selectbox("Marque", brand_names,index = 0)
    return brand_name

def get_displays_from_compare_csv():
    csv_filepath = os.path.join("models" ,"model_ccfl.csv")
    displays = list()
    with open(csv_filepath, "r", newline="") as csv_file:
        reader = csv.reader(csv_file, delimiter=",")
        next(reader)
        for row in reader:
            displays.append((row[0],row[1],row[2]))
    return displays

def exclude_dbb(model_years_bdd: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    """ remove specific models from lcd compare bdd if these models can confuse the search for other models"""
    LIST_MODELLS_TO_REMOVE = ["0", "1", "2", "3", "4", "10", "9", "5", "6", "8", "7"]
    return [model_year for model_year in model_years_bdd if model_year[1] not in LIST_MODELLS_TO_REMOVE]

def get_max_len_str_from_tuple(str_ints: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
    """ read the tuple from the list and keep only the tuple with the longest
    first element (string type) """
    max_len = 0
    for str_int in str_ints:
        len_text = len(str_int[0])
        max_len = len_text if len_text > max_len else max_len
    return [str_int for str_int in str_ints if len(str_int[0]) == max_len]

def get_lcd_ccfl(
    text: str, model_retros_bdd: List[Tuple[str, str, str]]
) -> Tuple[List[Tuple[str, str, str]], List[str]]:
    models = list()
    model_retros = list()
    for model_retro in model_retros_bdd:
        if model_retro[1] in text:
            model_retros.append(model_retro)
    model_retros = get_max_len_str_from_tuple(model_retros)
    print("before ", model_retros)
    retros = [model_retro[1:] for model_retro in model_retros]
    models = [model_retro[0].lower() for model_retro in model_retros]
    print("after ", retros)
    return list(set(retros)), list(set(models))

st.header("Détection LED /CCFL")
img_file_buffer = st.camera_input("Prenez une plaque signalétique d'un écran en photo")

if img_file_buffer is not None:
    # To read image file buffer as bytes:
    bytes_data = img_file_buffer.getvalue()

    # run ocr with google vision for text and document
    text, _ = google_vision_ocr.structure_google_vision_return(bytes_data, TEXT_DETECTION)
    document, _ = google_vision_ocr.structure_google_vision_return(bytes_data, DOCUMENT_TEXT_DETECTION)
    ocr_json = {"ocr_text": text, "ocr_document": document}
    full_text = extract_full_text_from_ocr_objects([ocr_json])
    if full_text:
        #st.write(full_text)
        models = get_displays_from_compare_csv()
        models = exclude_dbb(models)

        res = get_lcd_ccfl(full_text,models)
        if res[0]:
            st.write(f"Marque : {res[1]}")
            st.write(f"Modèle : {res[0][0][0]}")
            st.markdown(f"Rétro éclairage : **{res[0][0][1]}**")
        else:
            st.write("Information rétro éclairage non trouvée")
    else:
        st.write("Pas de plaque détectée")

