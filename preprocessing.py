import pandas as pd
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
import json

class Preprocessor:
    def __init__(self):
        self.encoders = {}
        self.mapping_table = pd.DataFrame()

    def one_hot_encode(self, df, columns):
        encoder = OneHotEncoder(sparse_output=False)
        encoded_cols = encoder.fit_transform(df[columns])
        encoded_df = pd.DataFrame(encoded_cols, columns=encoder.get_feature_names_out(columns))
        self.encoders['one_hot'] = encoder
        return pd.concat([df.drop(columns, axis=1), encoded_df], axis=1)

    def label_encode(self, df, columns):
        for col in columns:
            encoder = LabelEncoder()
            df[col] = encoder.fit_transform(df[col])
            self.encoders[col] = encoder
            # Save encoder classes to a file
            with open(f'{col}_encoder_classes.json', 'w') as f:
                json.dump(encoder.classes_.tolist(), f)
        return df

    def preprocess(self, df, one_hot_columns=None, label_encode_columns=None):
        if one_hot_columns:
            df = self.one_hot_encode(df, one_hot_columns)
        if label_encode_columns:
            df = self.label_encode(df, label_encode_columns)
        
        self.mapping_table = df.copy()
        return df, self.mapping_table

# Example usage:
# df = pd.read_csv('playground-series-s4e10/train.csv')
# preprocessor = Preprocessor()
# processed_df, mapping_table = preprocessor.preprocess(df, one_hot_columns=['person_home_ownership'], label_encode_columns=['cb_person_default_on_file'])