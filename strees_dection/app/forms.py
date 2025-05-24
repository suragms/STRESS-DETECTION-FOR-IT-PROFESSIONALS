from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['feedback_text', 'rating']
        widgets = {
            'feedback_text': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Enter your feedback here...',
                'required': True,
                'class': 'form-control',
                'aria-label': 'Feedback text'
            }),
            'rating': forms.RadioSelect(attrs={
                'required': True,
                'class': 'rating-radio',
                'aria-label': 'Rating selection'
            }),
        }
        error_messages = {
            'feedback_text': {
                'required': 'Feedback text is required.',
            },
            'rating': {
                'required': 'Rating is required.',
            },
        }

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]  # Choices for 1–5 stars
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'rating-radio'}),
        required=True
    )

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is not None:
            try:
                rating = int(rating)  # Convert to integer since ChoiceField returns string
                if rating < 1 or rating > 5:
                    raise forms.ValidationError('Rating must be between 1 and 5.')
            except ValueError:
                raise forms.ValidationError('Invalid rating value.')
        return rating