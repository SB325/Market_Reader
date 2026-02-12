pipeline {
    agent any
    stages {
        stage('Build Docker Images') {
            steps {
                script {
                    echo 'Building the application...' 
                    sh 'cd ../../'
                    sh """
                        docker compose build \\
                        extract_facts_filings \\
                        extract_submissions_filings \\
                        tl_submissions_filings \\
                        tl_facts_filings
                    """
                }
            }
        }
        stage('Run Docker Images') {
            steps {
                script { 
                    // Running application in test mode which confirms
                    // that imports work correctly
                    echo 'Running the application...' 
                    sh """
                        docker compose run --rm -d -e TEST_MODE \\
                        extract_facts_filings 
                        docker compose run --rm -d -e TEST_MODE  \\
                        extract_submissions_filings 
                        docker compose run --rm -d -e TEST_MODE  \\
                        tl_submissions_filings 
                        docker compose run --rm -d -e TEST_MODE  \\
                        tl_facts_filings 
                    """
                }
            }
        }
        stage('Deploy Images to registry') {
            steps {
                script { 
                    // Running application in test mode which confirms
                    // that imports work correctly
                    echo 'Deploying the application to registry...' 
                    sh """
                        docker tag homeserver-extract_facts_filings \\
                        localhost:5000/market_reader/etl/extract_facts_filings
                        docker push localhost:5000/market_reader/etl/extract_facts_filings

                        docker tag homeserver-extract_submissions_filings \\
                        localhost:5000/market_reader/etl/extract_submissions_filings
                        docker push localhost:5000/market_reader/etl/extract_submissions_filings
                        
                        docker tag homeserver-tl_facts_filings    \\
                        localhost:5000/market_reader/etl/tl_facts_filings   
                        docker push localhost:5000/market_reader/etl/tl_facts_filings

                        docker tag homeserver-tl_submissions_filings \\
                        localhost:5000/market_reader/etl/tl_submissions_filings
                        docker push localhost:5000/market_reader/etl/tl_submissions_filings
                    """
                }
            }
        }
    }
}