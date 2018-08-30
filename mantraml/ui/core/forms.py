from django import forms

class DeleteTrialForm(forms.Form):
    trial_hash = forms.CharField(widget = forms.HiddenInput(), label='trial_hash', max_length=64, required=False)

class DeleteTrialGroupForm(forms.Form):
    trial_group_hash = forms.CharField(widget = forms.HiddenInput(), label='trial_group_hash', max_length=64, required=False)

class StartInstanceForm(forms.Form):
    start_instance_id = forms.CharField(widget = forms.HiddenInput(), label='start_instance_id', required=False)

class StopInstanceForm(forms.Form):
    stop_instance_id = forms.CharField(widget = forms.HiddenInput(), label='stop_instance_id', required=False)

class TerminateInstanceForm(forms.Form):
    terminate_instance_id = forms.CharField(widget = forms.HiddenInput(), label='terminate_instance_id', required=False)