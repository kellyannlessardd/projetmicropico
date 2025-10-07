# SED-1515-Controle-et-Analyse-de-Signaux-PWM

Ce projet vise à concevoir deux programmes Python embarqués sur des dispositifs Raspberry 
Pi Pico. Le premier Pico génère un signal PWM avec un rapport cyclique variable. Le second 
Pico mesure la valeur moyenne du signal via un filtre RC et l’ADC, puis communique la valeur mesurée au premier Pico via une liaison série UART. L’objectif est d’évaluer la précision du signal PWM et d’afficher la différence entre la valeur souhaitée et la valeur mesurée. 
