from django.db import models

# Create your models here.

class Persona(models.Model):
    id = models.IntegerField(auto_created=True, primary_key=True)
    name = models.CharField(max_length=20)
    segment = models.CharField(max_length=50)
    age_group = models.CharField(max_length=10, help_text="예: 30대")
    family_structure = models.CharField(max_length=50, help_text="예: 1인 가구")
    gender = models.CharField(max_length=10, help_text="예: 여성")
    customer_value = models.CharField(max_length=50, help_text="예: 웰빙형")
    purchase_pattern = models.JSONField(max_length=100, help_text="예: 온라인 쇼핑 선호")
    lifestyle = models.JSONField(max_length=100, help_text="예: 액티브")
    job = models.CharField(max_length=50, help_text="예: 직장인")
    persona_summary_tag = models.TextField(max_length=500, help_text="예: 30대 여성, 웰빙형")

    def __str__(self):
        # 객체를 문자열로 표현할 때 사용합니다.
        # 예: '30대 여성 웰빙형'
        # return f"{self.age_group} {self.gender} {self.lifestyle} 페르소나"
        return f"{self.segment} - 페르소나 {self.id} {self.name}"

    class Meta:
        verbose_name_plural = "페르소나" # Django 관리자 페이지에서 보여지는 이름