# Logistic Regression

This model implements a simple logistic regression classifier in Keras. Here is how to use:

```
mantra train log_reg --dataset my_data --target my_target --features feature_1 feature_2
```

The above will use **my_target** as the \\(y\\) variable, and use the feature columns ['feature_1', 'feature_2'] for the \\(X\\) variable.

If you want evaluation scores on a validation or test set, then one task you can use is the default **binary_crossent** task which implements a binary crossentropy evaluation metric, and also reports the accuracy of the classifier:

```
mantra train log_reg --dataset my_data --task binary_crossent --target my_target --features feature_1 feature_2
```