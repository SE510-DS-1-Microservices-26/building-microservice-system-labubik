import logging
from typing import Optional
from uuid import UUID

import httpx

from app.core.application.interfaces import WorkflowRepository
from app.core.domain import WorkflowInstance, WorkflowState, WorkflowType

logger = logging.getLogger(__name__)


class WorkflowService:
    def __init__(self, repository: WorkflowRepository, core_service_url: str = ""):
        self.repository = repository
        self.core_service_url = core_service_url.rstrip("/")

    #  Public API

    def start_place_order(self, payload: dict) -> WorkflowInstance:
        """
        Saga: place-order
          Step 1 — create order  (POST /core-items)
          Step 2 — confirm order (PATCH /core-items/{id}/status → pending)
          Compensation — cancel order if step 2 fails
        """
        workflow = WorkflowInstance(
            workflow_type=WorkflowType.PLACE_ORDER,
            payload=payload,
        )
        self.repository.save(workflow)
        logger.info("Workflow %s started", workflow.workflow_id)

        try:
            order = self._create_order(payload)
        except Exception as exc:
            error_msg = f"Step 1 (create order) failed: {exc}"
            logger.error(error_msg)
            workflow.transition(WorkflowState.FAILED, error=error_msg)
            self.repository.save(workflow)
            return workflow

        workflow.payload["order_id"] = str(order["id"])
        workflow.transition(WorkflowState.ORDER_CREATED)
        self.repository.save(workflow)
        logger.info("Workflow %s — order %s created", workflow.workflow_id, order["id"])

        try:
            self._confirm_order(order["id"])
        except Exception as exc:
            error_msg = f"Step 2 (confirm order) failed: {exc}"
            logger.error(error_msg)
            workflow.transition(WorkflowState.COMPENSATING, error=error_msg)
            self.repository.save(workflow)

            # Compensation: cancel the order that was already created
            try:
                self._cancel_order(order["id"])
                workflow.transition(WorkflowState.CANCELLED, error=error_msg)
            except Exception as comp_exc:
                comp_error = f"{error_msg} | compensation also failed: {comp_exc}"
                logger.error(comp_error)
                workflow.transition(WorkflowState.FAILED, error=comp_error)

            self.repository.save(workflow)
            return workflow

        workflow.transition(WorkflowState.ORDER_CONFIRMED)
        self.repository.save(workflow)
        logger.info("Workflow %s — order confirmed", workflow.workflow_id)

        workflow.transition(WorkflowState.COMPLETED)
        self.repository.save(workflow)
        logger.info("Workflow %s completed successfully", workflow.workflow_id)
        return workflow

    def get_workflow(self, workflow_id: UUID) -> Optional[WorkflowInstance]:
        return self.repository.get_by_id(workflow_id)

    #  Private helpers — HTTP calls to core-service
    def _create_order(self, payload: dict) -> dict:
        url = f"{self.core_service_url}/core-items"
        body = {
            "customer_name": payload["customer_name"],
            "item_name": payload["item_name"],
            "quantity": payload["quantity"],
            "price": payload["price"],
            "owner_user_id": str(payload["owner_user_id"]),
        }
        response = httpx.post(url, json=body, timeout=5.0)
        if response.status_code != 201:
            raise RuntimeError(
                f"core-service returned {response.status_code}: {response.text}"
            )
        return response.json()

    def _confirm_order(self, order_id: str) -> dict:
        url = f"{self.core_service_url}/core-items/{order_id}/status"
        response = httpx.patch(url, json={"status": "pending"}, timeout=5.0)
        if response.status_code != 200:
            raise RuntimeError(
                f"core-service returned {response.status_code}: {response.text}"
            )
        return response.json()

    def _cancel_order(self, order_id: str) -> dict:
        url = f"{self.core_service_url}/core-items/{order_id}/status"
        response = httpx.patch(url, json={"status": "cancelled"}, timeout=5.0)
        if response.status_code != 200:
            raise RuntimeError(
                f"core-service returned {response.status_code} during compensation: {response.text}"
            )
        return response.json()
