from neo4j import GraphDatabase
import os

driver = None

def init_neo4j(uri, username, password):
    global driver
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
def get_driver():
    return driver

def close_driver():
    if driver:
        driver.close()