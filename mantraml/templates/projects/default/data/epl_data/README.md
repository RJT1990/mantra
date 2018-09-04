# Premier League Data

This dataset contains historical **Premier League** results as well as some arbitrary features. You can change the default target and features in the data.py file.

Alternatively you can use custom arguments through the command line, e.g:

```
mantra train my_model --dataset epl_data --target my_target --features feature_3 feature_4
```

The above will use **my_target** as the \\(y\\) variable, and use the feature columns ['feature_3', 'feature_4'] for the \\(X\\) variable.