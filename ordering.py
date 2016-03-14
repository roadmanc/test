import threading
import Queue
import time

class inventoryController(object):
    """
    inventory controller class to whole logic to manage inventory.
    """

    def __init__(self, **items):
        self.inventory = {}
        self.order_records = []
        for item in items:
            self.inventory[item] = int(items[item])
        self.product_list = self.inventory.keys()
        self.product_list.sort()
        self.order_log = []

    def get_product_list(self):
        return self.product_list

    def ordering(self, order):
        """
        verify order to make sure they are not zero or more than 5.
        Then, paste the order
        """

        header = order["Header"]
        lines = order["Lines"]
        if self._verify_order(lines):
            order_status = self._paste_order(lines)
            self._update_order_log(header, lines, order_status)
        else:
            return False

    def inventory_empty(self):
        """
        check if the inventory is empty or not
        """

        empty = True
        for item in self.inventory:
            if self.inventory[item] != 0:
                empty = False
                break
        return empty

    def _update_order_log(self, header, lines, order_status):
        """
        tracking the order log
        """

        quantity_on_each_line = self._parse_quantity(lines)
        quantity_allocated = self._parse_quantity_allocated(order_status)
        quantity_backordered = self._parse_backordered(order_status)
        log_entry = "{}: {}".format(header,"::".join([quantity_on_each_line,quantity_allocated,quantity_backordered]))
        self.order_log.append(log_entry)

    def _parse_quantity(self, lines):
        output = []
        for product in self.product_list:
            for line in lines:
                if line["Product"] == product:
                    #line_log.append(line["Quantity"])
                    output.append(line["Quantity"])
                    break
            else:
                output.append("0")
        return ",".join(output)

    def _parse_quantity_allocated(self, order_status):
        output = []
        for product in self.product_list:
            for order in order_status:
                order_product, order_details = order.keys()[0], order.values()[0]
                is_order,quantity = order_details.split(":")
                if order_product == product and is_order == "ordered":
                    output.append(quantity)
                    break                  
            else:
                output.append("0")        
        return ",".join(output)

    def _parse_backordered(self, order_status):
        output = []
        for product in self.product_list:
            for order in order_status:
                order_product, order_details = order.keys()[0], order.values()[0]
                is_order,quantity = order_details.split(":")
                if order_product == product and is_order == "backordered":
                    output.append(quantity)
                    break
            else:
                output.append("0")
        return ",".join(output)

    def _paste_order(self, lines):
        order_status = []
        for line in lines:
            product = line["Product"]
            quantity = int(line["Quantity"])
            if self.inventory[product] >= quantity:
                self.inventory[product] -= quantity
                order_status.append({product:"ordered:{}".format(quantity)})
            else:
                order_status.append({product:"backordered:{}".format(quantity)})
        return order_status
   
    def _verify_order(self,lines):
        for line in lines:
            if int(line["Quantity"]) <=0 or int(line["Quantity"]) > 5:
                 print "This is an invalid order: %s" % (line)
                 return False

        return True

    def __str__(self):
        result = "" 
        for item in self.product_list:
            result += "Product: {} Quantity: {}\n".format(item, self.inventory[item])

        return result

class order_client(threading.Thread):
    """
    client class to simulate the client to make order
    """

    def __init__(self, header, inventory, order_queue, lock):
        super(order_client, self).__init__()
        self.header = header
        self.inventory = inventory
        self.order_queue = order_queue
        self.lock = lock

    def run(self):
        self.make_order()

    def make_order(self):
        global exitFlag
        while not exitFlag:
            self.lock.acquire()
            if not self.order_queue.empty():
                order = self.order_queue.get()
                self.inventory.ordering({"Header": self.header, "Lines":order["Lines"]})
                if self.inventory.inventory_empty():
                    self.order_queue.queue.clear()
                time.sleep(1)
            self.lock.release()


# testing starting
inventory = inventoryController(A=2,B=3,C=1,D=0,E=0)

#display the inventory
print "Current Inventory:"
print inventory

lock = threading.Lock()
workQueue = Queue.Queue(100)
running_clients = []

#number of simulated clients
num_test_clients = 6
client_list = [str(x) for x in xrange(1,num_test_clients+1)]
exitFlag = 0

#test order data
test_order_list = [{"Lines":[{"Product": "A", "Quantity": "1"}, {"Product": "C", "Quantity": "1"}]},
                   {"Lines":[{"Product": "E", "Quantity": "5"}]},
                   {"Lines":[{"Product": "D", "Quantity": "4"}]},
                   {"Lines":[{"Product": "A", "Quantity": "1"}, {"Product": "C", "Quantity": "1"}]},
                   {"Lines":[{"Product": "B", "Quantity": "3"}]},
                   {"Lines":[{"Product": "D", "Quantity": "4"}]}]

# display simulated order list
print "below is the simulated orders"
for line in test_order_list:
    print "%s" % (line)

#start client threads
for id in client_list:
    client = order_client(id,inventory,workQueue,lock)
    client.start()
    running_clients.append(client)

#populate order in queue
lock.acquire()
for order in test_order_list:
    workQueue.put(order)
lock.release()

#if no more order in queue, set exit flag to let the client stop
#it could be the inventory is empty so the order queue were empty early

while not workQueue.empty():
    pass
else:
    exitFlag = 1

for running_client in running_clients:
    running_client.join()

#display tracking
print "Order tracking logs"
for entry in inventory.order_log:
    print entry
