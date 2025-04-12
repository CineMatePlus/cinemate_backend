@echo off
echo ================================
echo  Allure Raporlu Behave Testleri
echo ================================

poetry run behave tests/features -f allure_behave.formatter:AllureFormatter -o allure-results
allure generate allure-results -o allure-report --clean
allure open allure-report
