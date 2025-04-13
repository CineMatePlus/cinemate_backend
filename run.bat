@echo off
echo ================================
echo  Allure Raporlu Behave Testleri
echo ================================

poetry run behave tests/features -f allure_behave.formatter:AllureFormatter -o tests/allure-results
allure generate tests/allure-results -o tests/allure-report --clean
allure open tests/allure-report
