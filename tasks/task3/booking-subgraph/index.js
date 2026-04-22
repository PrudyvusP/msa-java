import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { buildSubgraphSchema } from '@apollo/subgraph';
import gql from 'graphql-tag';

const typeDefs = gql`
  type Booking @key(fields: "id") {
    id: ID!
    userId: String!
    hotelId: String!
    promoCode: String
    discountPercent: Int
    hotel: Hotel
  }

  # Ссылка на внешнюю сущность из hotel-subgraph
  extend type Hotel @key(fields: "id") {
    id: ID! @external
  }

  type Query {
    bookingsByUser(userId: String!): [Booking]
  }
`;

// TODO: заменить на gRPC-вызов к booking-service из задания 2
const bookings = [
  { id: 'b1', userId: 'user1', hotelId: 'h1', promoCode: 'SUMMER', discountPercent: 20 },
  { id: 'b2', userId: 'user1', hotelId: 'h2', promoCode: null, discountPercent: 0 },
  { id: 'b3', userId: 'user2', hotelId: 'h1', promoCode: 'WINTER', discountPercent: 15 },
];

const resolvers = {
  Query: {
    bookingsByUser: async (_, { userId }, { req }) => {
      const authenticatedUserId = req.headers['userid'];
      console.log(`[ACL] Запрос: requester="${authenticatedUserId}", target="${userId}"`);

      if (!authenticatedUserId) {
        console.log('[ACL] Deny: отсутствует заголовок userid');
        throw new Error('Unauthorized: userid header is required');
      }
      if (authenticatedUserId !== userId) {
        console.log(`[ACL] Deny: requester=${authenticatedUserId} tried to access userId=${userId}`);
        throw new Error('Forbidden: you can only view your own bookings');
      }

      console.log(`[ACL] Allow: userId=${userId}`);
      return bookings.filter((b) => b.userId === userId);
    },
  },
  Booking: {
    // Возвращаем ссылку на Hotel — Apollo Federation сам разрешит её через hotel-subgraph
    hotel: (booking) => ({ __typename: 'Hotel', id: booking.hotelId }),
  },
};

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
});

startStandaloneServer(server, {
  listen: { port: 4001 },
  context: async ({ req }) => ({ req }),
}).then(() => {
  console.log('✅ Booking subgraph ready at http://localhost:4001/');
});
