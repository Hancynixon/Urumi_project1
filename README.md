Multi-Tenant Store Provisioning Platform (Kubernetes + Helm)



**1. Problem Statement**



This project implements a Kubernetes-native multi-tenant store provisioning system.



The objective is to dynamically create isolated online stores using an API. Each store runs independently inside its own Kubernetes namespace and is exposed via host-based routing.



For example, after provisioning a store, it becomes accessible at:



**http://store-7016ff.localhost/**





**The system is designed to demonstrate:**



* Multi-tenant isolation
* Helm-based automation
* Persistent storage handling
* Ingress routing
* Clear separation between control plane and data plane







**2. System Architecture Overview**	



The architecture is divided into two main parts:



**Control Plane**



Implemented using FastAPI.



**Responsibilities:**



* Create store (**POST /stores**)
* Delete store (**DELETE /stores/{store\_id}**) 
* List stores (**GET /stores**)
* Audit log (**GET /audit**)
* Enforce max store guardrail (5 stores)
* Wait for readiness before returning success



The control plane does not manually create pods. It triggers Helm installations, which makes the provisioning process declarative and consistent.



**Data Plane (Per Store Namespace)**



Each store is deployed inside its own namespace:



For example:



**store-7016ff**



**Inside that namespace:**



* WordPress Deployment
* MariaDB StatefulSet
* PersistentVolumeClaims
* ClusterIP Services
* Ingress resource



This ensures strong isolation between stores.



If one store crashes or is deleted, other stores remain unaffected.





**3. Provisioning Flow (Example: store-7016ff)**



When **POST /stores** is called:



* A unique store ID is generated (e.g., **store-7016ff**).
* A namespace **store-7016ff** is created.
* A Helm wrapper chart is installed.
* Ingress hostname is set to:

&nbsp;   

&nbsp; 	 **store-7016ff.localhost** 



* Backend waits until pods become 1/1 Ready.
* The API returns:



&nbsp;  **{**

  **"store\_id": "store-7016ff",**

  **"status": "Ready",**

  **"url": "http://store-7016ff.localhost"**

**}**

 



**Deletion works by:**



* Helm uninstall
* Namespace deletion



Deleting the namespace removes all associated resources.





**4. Store Engine**



**WooCommerce (WordPress + MariaDB)**



End-to-end functionality verified:



* Open storefront
* Add product to cart
* Checkout using Cash on Delivery
* Confirm order created



Architecture allows adding another engine in future by extending the Helm wrapper.





**5. Helm Design**



Instead of directly installing the Bitnami WordPress chart, a wrapper Helm chart was created:



   **helm/store/**





**This wrapper:**



* Uses Bitnami WordPress as dependency
* Allows dynamic ingress hostname override
* Separates environment configuration



**Two values files are defined:**



* **values-local.yaml**
* **values-prod.yaml (for VPS deployment)**



I chose a wrapper chart instead of direct installation to maintain better control and extensibility.







**6. Ingress Architecture**



* Default Traefik (bundled with k3s) was disabled to avoid multiple ingress controllers running simultaneously.
* NGINX Ingress Controller was installed explicitly.
* Routing works like:



&nbsp;	**store-7016ff.localhost → store-7016ff namespace**



* Port 80 from the host machine is mapped to the k3d load balancer.
* This enables host-based multi-store routing in a clean and controlled way.







**7. Storage Design**



MariaDB runs as a StatefulSet with PersistentVolumeClaims.



**This ensures:**



* Data survives pod restarts
* Each store has its own isolated database
* Data is automatically removed when namespace is deleted



Using StatefulSet ensures stable identity and storage consistency.





**8. Guardrails Implemented**



The following safety mechanisms are included:



* Maximum store limit (5 stores)
* Idempotency check for namespace existence
* Readiness polling before returning success
* Basic audit logging endpoint



These mechanisms improve reliability and prevent uncontrolled resource usage.



**9. API Endpoints**



**POST /stores**



Creates a new store and returns URL.



**Example response:**



**{**

  **"store\_id": "store-7016ff",**

  **"status": "Ready",**

  **"url": "http://store-7016ff.localhost"**

**}**



**GET /stores**



Lists all active stores and their status.



**DELETE /stores/{store\_id}**



Deletes the store and cleans its namespace.



**GET /audit**



Returns provisioning event history.





**10. Local Setup Instructions**



* Step 1: Create k3d Cluster (Disable Traefik)



&nbsp;	**k3d cluster create urumi --k3s-arg "--disable=traefik@server:0" -p "80:80@loadbalancer" -p "443:443@loadbalancer"**



* Step 2: Install NGINX Ingress

&nbsp;	**helm install ingress-nginx ingress-nginx/ingress-nginx \\**

  	  **--namespace ingress-nginx \\**

  	  **--create-namespace \\**

     	  **--set controller.service.type=LoadBalancer \\**

  	  **--set controller.ingressClassResource.default=true**

&nbsp;	

&nbsp;	Wait until: **kubectl get pods -n ingress-nginx** Shows controller pod as **1/1 Running**.





* Step 3: Start Backend 

&nbsp;	**cd backend**

	**python -m venv venv**

	**venv\\Scripts\\activate**

	**pip install -r requirements.txt**

	**uvicorn main:app --reload**

 

**Open:**



 	**http://127.0.0.1:8000/docs**



* Step 4 – Start Dashboard



&nbsp;	**cd dashboard**

	**npm install**

	**npm start**



**Open:**



 	**http://localhost:3000**







**11. How to Create a Store and Place an Order**



* Open Dashboard:

&nbsp;	**http://localhost:3000**



* Click Create New Store
* Wait until status becomes **Ready**
* Click **Open Store**
* Add product to cart
* Checkout using Cash on Delivery
* Confirm order received page



Optional verification via CLI:



	**kubectl exec -it <wordpress-pod> -n store-7016ff -- wp wc order list --user=1**





**12. VPS / Production-Like Deployment (k3s)**



The same Helm chart can be deployed on a VPS running k3s.



Changes required via **values-prod.yaml**:



* Real DNS (e.g., store.example.com)
* Production storage class
* TLS via cert-manager
* External LoadBalancer or reverse proxy
* Proper secrets management



**Example:**



	**helm install store-7016ff ./helm/store -f values-prod.yaml**





No structural change required in Helm chart.





**13. System Design \& Tradeoffs**



**Architecture Choice**



Namespace-per-store was chosen for:



* Strong isolation
* Clean teardown
* Clear resource boundaries
* Simple multi-tenant separation



Helm wrapper chart chosen for:



* Extensibility
* Environment separation
* Cleaner production transition







**Idempotency \& Failure Handling**



* Namespace existence check prevents duplicate creation
* Max store guardrail prevents abuse
* Readiness polling ensures only Ready state returned
* Namespace deletion guarantees full cleanup



Failure handling is basic; advanced reconciliation controller is future work.





**14. Production Changes**



For production:



* Replace localhost with real DNS
* Enable TLS via cert-manager
* Use production-grade storage class
* Add ResourceQuota \& LimitRange
* Add RBAC least privilege
* Add HPA for scaling backend
* Add persistent logging	





**15. Repository Structure**



	**backend/**

	**dashboard/**

	**helm/**

  	  **store/**

    	  **Chart.yaml**

    	  **values-local.yaml**

          **values-prod.yaml**

	**README.md**





**16. Conclusion**



This project demonstrates:	

* Kubernetes-native multi-tenant provisioning
* Namespace-level isolation
* Helm-based deployment automation
* Persistent storage management
* Host-based ingress routing
* Basic guardrails and reliability mechanisms



The system is designed to be extendable and portable across environments.

















