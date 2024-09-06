def create_docker_compose_settings(abs_path, port=None, seedFinder_query="", db_crawl="", coll_crawl="", db_prod="", coll_prod="", coll_voc="", coll_topic_vec="", db_ip="", db_user="", db_pass="", misp_ip="", misp_key="", cr_config=None, ner_config=None, mongo=False, crawler_id="", crawler_type="", post_window=0):

    if cr_config is not None:
        settings_list = [
            {
                "type": "content_ranking",
                "obj": {
                    "version": "2",
                    "services": {
                        "content-ranking": {
                            "image": "content-ranking",
                            "entrypoint": "python3 content_rank.py calc-score --ip=\"{}\" --username=\"{}\" --password=\"{}\" --db_crawl=\"{}\" --collection_crawl=\"{}\" --collection_voc=\"{}_top{}\" --collection_topic_vec=\"{}{}\" --topn={} --iteration={} --post_window={}".format(
                                db_ip, db_user, db_pass,
                                db_crawl, coll_crawl,
                                coll_voc, cr_config["top_n"],
                                coll_topic_vec, cr_config["top_n"],
                                cr_config["top_n"],
                                cr_config["iteration"],
                                cr_config["number_of_docs"]
                            ),
                            "volumes": [
                                "./data/:/content-ranking/data"
                            ]
                        }
                    }
                }
            }
        ]
    elif ner_config is not None:
        settings_list = [
            {
                "type": "ner",
                "obj": {
                    "version": "2",
                    "services": {
                        "named-entity-recognition": {
                            "image": "named-entity-recognition",
                            "entrypoint": "python3 ner.py get-ents --ip=\"{}\" --username=\"{}\" --password=\"{}\" --misp_ip=\"http://{}\" --misp_key=\"{}\" --db_crawl=\"{}\" --collection_crawl=\"{}\" --db_products=\"{}\" --collection_products=\"{}\" --spacy_model=\"{}\" --phrase_matcher={} --topn={} --iteration={} --post_window={}".format(
                                db_ip, db_user, db_pass, misp_ip, misp_key,
                                db_crawl, coll_crawl, db_prod, coll_prod,
                                ner_config["spacy_model"],
                                ner_config["phrase_matcher"],
                                ner_config["top_n"],
                                ner_config["iteration"],
                                ner_config["number_of_docs"]
                            ),
                            "volumes": [
                                "./data/:/named-entity-recognition/data",
                                "./model/:/named-entity-recognition/model"
                            ]
                        }
                    }
                }
            }
        ]
    elif mongo is True:
        settings_list = [
            {
                "type": "mongo",
                "obj": {
                    "version": "3.1",
                    "services": {
                        "mongo": {
                            "image": "mongo",
                            "environment": {
                                "MONGO_INITDB_ROOT_USERNAME": db_user,
                                "MONGO_INITDB_ROOT_PASSWORD": db_pass
                            },
                            "ports": [
                                "27017:27017"
                            ],
                            "volumes": [
                                "./data:/data/db"
                            ]
                        },
                        "mongo-express": {
                            "image": "mongo-express",
                            "ports": [
                                "8081:8081"
                            ],
                            "environment": {
                                "ME_CONFIG_MONGODB_ADMINUSERNAME": db_user,
                                "ME_CONFIG_MONGODB_ADMINPASSWORD": db_pass
                            }
                        }
                    }
                }
            }
        ]
    else:
        settings_list = [
            {
                "type": "focused",
                "obj": {
                    "version": "2",
                    "services": {
                        "ache": {
                            "entrypoint": "sh -c 'sleep 10 && /ache/bin/ache startCrawl -c /config/ -s /config/seeds.txt -o /data/ -m /config/model/'",
                            "image": "vidanyu/ache",
                            "ports": [
                                str(port) + ":8080"
                            ],
                            "volumes": [
                                "./data-ache/:/data",
                                "./:/config"
                            ]
                        }
                    }
                }
            },
            {
                "type": "indepth_clear",
                "obj": {
                    "version": "2",
                    "services": {
                        "ache": {
                            "entrypoint": "sh -c 'sleep 10 && /ache/bin/ache startCrawl -c /config/ -s /config/seeds.txt -o /data'",
                            "image": "vidanyu/ache",
                            "ports": [
                                str(port) + ":8080"
                            ],
                            "volumes": [
                                "./data-ache/:/data",
                                "./:/config"
                            ]
                        }
                    }
                }
            },
            {
                "type": "indepth_dark",
                "obj": {
                    "version": "2",
                    "services": {
                        "ache": {
                            "depends_on": [
                                "torproxy"
                            ],
                            "entrypoint": "sh -c 'sleep 10 && /ache/bin/ache startCrawl -c /config/ -s /config/tor.seeds -o /data -e tor'",
                            "image": "vidanyu/ache",
                            "links": [
                                "torproxy"
                            ],
                            "ports": [
                                str(port) + ":8080"
                            ],
                            "volumes": [
                                "./data-ache/:/data",
                                "./:/config"
                            ]
                        },
                        "torproxy": {
                            "image": "dperson/torproxy",
                            "ports": [
                                "8118:8118"
                            ]
                        }
                    }
                }
            },
            {
                "type": "watchers",
                "obj": {
                    "version": "2",
                    "services": {
                        "watchers": {
                            "image": "watchers",
                            "entrypoint": "python3 watcher.py start-watcher --ip=\"{}\" --username=\"{}\" --password=\"{}\" --db_crawl=\"{}\" --collection_crawl=\"{}\" --crawler_id=\"{}\" --crawler_type=\"{}\" --directory=\".\"".format(
                                db_ip, db_user, db_pass,
                                db_crawl, coll_crawl,
                                crawler_id, crawler_type
                            ),
                            "volumes": [
                                abs_path + "/data-ache/default/data_pages:/watchers/" + crawler_id + "/data-ache/default/data_pages"
                            ]
                        }
                    }
                }
            },
            {
                "type": "model_1",
                "obj": {
                    "version": "2",
                    "services": {
                        "ache": {
                            "entrypoint": "sh -c 'sleep 10 && /ache/bin/ache buildModel -t /model/training_data -o /model/'",
                            "image": "vidanyu/ache",
                            "ports": [
                                str(port) + ":8080"
                            ],
                            "volumes": [
                                "./:/model"
                            ]
                        }
                    }
                }
            },
            {
                "type": "model_2",
                "obj": {
                    "type": "smile",
                    "parameters": {
                        "features_file": "pageclassifier.features",
                        "model_file": "pageclassifier.model",
                        "relevance_threshold": 0.7
                    }
                }
            },
            {
                "type": "seedFinder",
                "obj": {
                    "version": "2",
                    "services": {
                        "ache": {
                            "entrypoint": "sh -c 'sleep 10 && /ache/bin/ache seedFinder --initialQuery \"" + seedFinder_query + "\" --modelPath /crawlerDir/model/ --seedsPath crawlerDir/'",
                            "image": "vidanyu/ache",
                            "ports": [
                                str(port) + ":8080"
                            ],
                            "volumes": [
                                "./../:/crawlerDir"
                            ]
                        }
                    }
                }
            },
            {
                "type": "ache_focused",
                "obj": {
                    "target_storage.data_format.type": "FILESYSTEM_HTML",
                    "target_storage.store_negative_pages": "false",
                    "target_storage.hard_focus": "true",
                    "target_storage.visited_page_limit": 10000000,
                    "target_storage.english_language_detection_enabled": "true",
                    "link_storage.max_pages_per_domain": 100000,
                    "link_storage.link_strategy.use_scope": "false",
                    "link_storage.link_strategy.outlinks": "true",
                    "link_storage.link_classifier.type": "LinkClassifierBaseline",
                    "link_storage.online_learning.enabled": "true",
                    "link_storage.online_learning.type": "FORWARD_CLASSIFIER_BINARY",
                    "link_storage.link_selector": "TopkLinkSelector",
                    "link_storage.max_size_cache_urls": 10000,
                    "link_storage.directory": "'data_url/dir'",
                    "link_storage.scheduler.host_min_access_interval": 5000,
                    "link_storage.scheduler.max_links": 10000,
                    "crawler_manager.downloader.user_agent.name": "ACHE",
                    "crawler_manager.downloader.user_agent.string": "'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'",
                    "crawler_manager.downloader.download_thread_pool_size": 100,
                    "crawler_manager.downloader.max_retry_count": 2,
                    "crawler_manager.downloader.valid_mime_types": [
                        "text/xml",
                        "text/html",
                        "text/plain",
                        "application/x-asp",
                        "application/xhtml+xml",
                        "application/vnd.wap.xhtml+xml"
                    ],
                    "crawler_manager.downloader.use_okhttp3_fetcher": "true",
                    "link_storage.download_sitemap_xml": "false"
                }
            },
            {
                "type": "ache_indepth",
                "obj": {
                    "target_storage.data_formats": [
                        "FILESYSTEM_HTML"
                    ],
                    "target_storage.data_format.filesystem.compress_data": "false",
                    "link_storage.link_strategy.use_scope": "true",
                    "link_storage.download_sitemap_xml": "true",
                    "link_storage.scheduler.host_min_access_interval": 2000
                }
            }
        ]

    return settings_list
